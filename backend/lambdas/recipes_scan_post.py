"""
POST /recipes/scan - Image-based health analysis Lambda.
Accepts image_base64 + optional text_description, user_concerns, allergies, diet_type.
Full pipeline: condition analysis -> nutrient lookup -> FDA foods -> preference filtering ->
AI food cleanup -> recipe search -> recipe filtering -> food images -> response assembly.
"""
import json
import boto3
from urllib.request import Request, urlopen
from urllib.parse import quote, urlencode
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

_secrets_cache = {}

def _get_secret(key):
    if not _secrets_cache:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId='remedi_api_keys')
        _secrets_cache.update(json.loads(resp['SecretString']))
    return _secrets_cache.get(key, '')


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _http_get(url, headers=None, timeout=15):
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _http_post(url, data, headers=None, timeout=30):
    req = Request(url, data=json.dumps(data).encode('utf-8'), headers=headers or {})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))


# ======================== CONDITION ANALYSIS ========================

CONDITION_ANALYSIS_PROMPT = """You are a health analysis assistant specializing in nutritional healing.

Analyze the user's health concern and categorize it. Return JSON:
{
    "condition_name": "Specific descriptive name",
    "condition_type": "category_from_list",
    "explanation": "Personalized explanation of the condition and how nutrition helps",
    "severity": "mild|moderate|concerning"
}

Categories: acne, dry_skin, eczema, psoriasis, rash, skin_inflammation, boil, sore, wound_healing,
bloating, constipation, acid_reflux, nausea, digestive_issues, fatigue, low_energy, brain_fog,
anxiety, stress, depression, insomnia, weak_immunity, cold_symptoms, flu_symptoms,
joint_pain, arthritis, muscle_pain, general_inflammation, high_blood_pressure, high_cholesterol,
heart_health, blood_sugar, diabetes_support, weight_loss, metabolism_boost, hair_loss,
eye_health, bone_health, allergies, headache, migraine"""


def _analyze_condition(image_base64, text_description, user_concerns):
    messages = [{'role': 'system', 'content': CONDITION_ANALYSIS_PROMPT}]
    user_parts = []
    if image_base64:
        user_parts.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}})
    text = ''
    if text_description:
        text += f'Description: {text_description}\n'
    if user_concerns:
        text += f'User concerns: {user_concerns}\n'
    if text:
        user_parts.append({'type': 'text', 'text': text})

    messages.append({'role': 'user', 'content': user_parts if image_base64 else text})

    try:
        resp = _http_post('https://api.openai.com/v1/chat/completions', {
            'model': 'gpt-4o-mini', 'messages': messages, 'max_tokens': 500, 'temperature': 0.7
        }, {'Content-Type': 'application/json', 'Authorization': f'Bearer {_get_secret("OPENAI_API_KEY")}'})
        result_text = resp['choices'][0]['message']['content']
        if result_text.startswith('```'):
            result_text = result_text.strip('`').replace('json', '', 1).strip()
        return json.loads(result_text)
    except Exception:
        return _fallback_analysis(text_description, user_concerns)


def _fallback_analysis(text_description, user_concerns):
    combined = f"{text_description or ''} {user_concerns or ''}".lower()
    keywords = {
        'acne': (['acne', 'pimple', 'breakout'], 'acne', 'Acne or breakout'),
        'dry_skin': (['dry skin', 'flaky', 'rough skin'], 'dry_skin', 'Dry skin'),
        'eczema': (['eczema', 'dermatitis'], 'eczema', 'Eczema'),
        'bloating': (['bloat', 'gas', 'gassy'], 'bloating', 'Bloating'),
        'fatigue': (['tired', 'fatigue', 'exhausted', 'no energy'], 'fatigue', 'Fatigue'),
        'anxiety': (['anxiety', 'anxious', 'nervous'], 'anxiety', 'Anxiety'),
        'headache': (['headache', 'migraine'], 'headache', 'Headache'),
        'cold': (['cold', 'flu', 'cough', 'sore throat'], 'cold_symptoms', 'Cold symptoms'),
        'joint': (['joint', 'arthritis', 'knee pain'], 'joint_pain', 'Joint pain'),
        'hair': (['hair loss', 'thinning hair'], 'hair_loss', 'Hair concerns'),
        'weight': (['weight', 'diet', 'lose weight'], 'weight_loss', 'Weight management'),
        'sleep': (['sleep', 'insomnia'], 'insomnia', 'Sleep difficulties'),
        'stress': (['stress', 'stressed'], 'stress', 'Stress'),
        'constipation': (['constipat'], 'constipation', 'Constipation'),
        'acid_reflux': (['heartburn', 'acid reflux'], 'acid_reflux', 'Acid reflux'),
    }
    for key, (kws, ctype, cname) in keywords.items():
        for kw in kws:
            if kw in combined:
                return {'condition_name': cname, 'condition_type': ctype,
                        'explanation': f'Based on your description, this appears to be {cname.lower()}. Nutritional support can help.',
                        'severity': 'mild'}
    return {'condition_name': 'General health concern', 'condition_type': 'general_inflammation',
            'explanation': 'Anti-inflammatory foods and a nutrient-rich diet can support your health.',
            'severity': 'mild'}


# ======================== NUTRIENT RECOMMENDATIONS ========================

NUTRIENT_DB = {
    'acne': {
        'nutrients': ['Zinc', 'Vitamin A', 'Omega-3', 'Vitamin E', 'Probiotics'],
        'nutrient_explanations': {
            'Zinc': 'Reduces sebum production and has antimicrobial properties against acne-causing bacteria. Studies show zinc deficiency worsens acne.',
            'Vitamin A': 'Regulates skin cell turnover, preventing pores from becoming clogged. The basis for prescription retinoid treatments.',
            'Omega-3': 'Reduces inflammatory markers that cause acne lesions to become red and swollen. Balances omega-6 fatty acids that promote inflammation.',
            'Vitamin E': 'Protects skin from oxidative damage and helps regulate sebum production to prevent clogged pores.',
            'Probiotics': 'Supports gut-skin axis health. Research shows gut microbiome imbalance is linked to acne severity.'
        },
        'foods': ['pumpkin seeds', 'sweet potato', 'salmon', 'almonds', 'yogurt']
    },
    'dry_skin': {
        'nutrients': ['Vitamin E', 'Omega-3', 'Vitamin A', 'Biotin', 'Vitamin C'],
        'nutrient_explanations': {
            'Vitamin E': 'Strengthens skin barrier function and locks in moisture. Reduces transepidermal water loss that causes dryness.',
            'Omega-3': 'Builds healthy cell membranes that retain moisture. Essential for maintaining skin hydration from within.',
            'Vitamin A': 'Promotes production of healthy skin cells and natural moisturizing factors in the epidermis.',
            'Biotin': 'Essential for fatty acid synthesis that creates the skin\'s natural oil barrier. Deficiency causes scaly, dry skin.',
            'Vitamin C': 'Required for collagen production which gives skin structure and water-holding capacity.'
        },
        'foods': ['avocado', 'walnuts', 'sweet potato', 'eggs', 'bell peppers']
    },
    'eczema': {
        'nutrients': ['Omega-3', 'Vitamin D', 'Probiotics', 'Vitamin E', 'Zinc'],
        'nutrient_explanations': {
            'Omega-3': 'Reduces inflammatory cytokines that trigger eczema flares. Clinical trials show improvement in skin hydration and reduced itching.',
            'Vitamin D': 'Modulates immune responses and strengthens skin barrier. Low vitamin D is strongly associated with eczema severity.',
            'Probiotics': 'Regulates immune system overreaction that causes eczema. Specific strains reduce eczema symptoms in clinical studies.',
            'Vitamin E': 'Reduces skin inflammation and oxidative stress. Helps repair damaged skin barrier characteristic of eczema.',
            'Zinc': 'Supports skin healing and immune regulation. Helps prevent secondary infections in damaged eczema skin.'
        },
        'foods': ['fatty fish', 'fortified milk', 'kefir', 'sunflower seeds', 'oysters']
    },
    'psoriasis': {
        'nutrients': ['Omega-3', 'Vitamin D', 'Selenium', 'Vitamin A', 'Zinc'],
        'nutrient_explanations': {
            'Omega-3': 'Reduces inflammatory compounds that cause rapid skin cell turnover in psoriasis. Fish oil studies show reduced plaque severity.',
            'Vitamin D': 'Slows excessive skin cell growth and modulates immune response. Topical vitamin D is an FDA-approved psoriasis treatment.',
            'Selenium': 'Antioxidant that reduces oxidative stress associated with psoriasis. Low selenium levels correlate with disease severity.',
            'Vitamin A': 'Normalizes skin cell differentiation and reduces hyperproliferation. Related to retinoid-based psoriasis medications.',
            'Zinc': 'Regulates immune function and supports healthy skin renewal. Helps prevent the excessive cell buildup of psoriasis.'
        },
        'foods': ['mackerel', 'sardines', 'brazil nuts', 'carrots', 'beef']
    },
    'rash': {
        'nutrients': ['Vitamin C', 'Vitamin E', 'Quercetin', 'Omega-3', 'Zinc'],
        'nutrient_explanations': {
            'Vitamin C': 'Strengthens blood vessel walls to reduce rash appearance. Supports immune function to fight underlying causes.',
            'Vitamin E': 'Protects skin cells from damage and accelerates healing of irritated skin.',
            'Quercetin': 'Natural antihistamine that reduces allergic reactions causing rashes. Stabilizes mast cells that release histamine.',
            'Omega-3': 'Reduces inflammatory response that causes redness and swelling in rash-affected areas.',
            'Zinc': 'Promotes skin healing and has anti-inflammatory properties to calm irritated skin.'
        },
        'foods': ['berries', 'nuts', 'onions', 'fish', 'legumes']
    },
    'skin_inflammation': {
        'nutrients': ['Vitamin E', 'Vitamin C', 'Omega-3', 'Zinc', 'Selenium'],
        'nutrient_explanations': {
            'Vitamin E': 'Protects skin cell membranes from oxidative damage and reduces inflammatory responses. FDA recognizes it as essential for skin barrier function.',
            'Vitamin C': 'Essential for collagen synthesis which repairs damaged skin tissue. Also acts as an antioxidant to neutralize inflammation-causing free radicals.',
            'Omega-3': 'Reduces production of inflammatory compounds (prostaglandins and leukotrienes) that cause skin redness and swelling.',
            'Zinc': 'Accelerates wound healing and regulates immune responses that contribute to inflammation. Deficiency is linked to skin disorders.',
            'Selenium': 'Works synergistically with Vitamin E to protect skin cells from oxidative stress and UV damage.'
        },
        'foods': ['almonds', 'citrus fruits', 'salmon', 'pumpkin seeds', 'brazil nuts']
    },
    'boil': {
        'nutrients': ['Vitamin C', 'Vitamin A', 'Zinc', 'Iron', 'Protein'],
        'nutrient_explanations': {
            'Vitamin C': 'Essential for immune function to fight bacterial infection causing boils. Supports collagen formation for skin healing.',
            'Vitamin A': 'Maintains skin barrier integrity and supports immune response against infection.',
            'Zinc': 'Critical for immune function and wound healing. Deficiency impairs the body\'s ability to fight skin infections.',
            'Iron': 'Required for immune cell function and tissue oxygenation during healing process.',
            'Protein': 'Provides amino acids needed for tissue repair and immune system antibody production.'
        },
        'foods': ['citrus fruits', 'carrots', 'spinach', 'beans', 'lean meat']
    },
    'sore': {
        'nutrients': ['Vitamin C', 'Vitamin B12', 'Iron', 'Folate', 'Zinc'],
        'nutrient_explanations': {
            'Vitamin C': 'Accelerates wound healing and collagen formation. Essential for tissue repair in mouth sores.',
            'Vitamin B12': 'Deficiency is a common cause of mouth sores. Supplementation often resolves recurrent canker sores.',
            'Iron': 'Iron deficiency anemia causes mouth sores. Adequate iron supports mucosal tissue health.',
            'Folate': 'Works with B12 for healthy cell division. Low folate is associated with recurrent oral sores.',
            'Zinc': 'Promotes mucosal healing and has antimicrobial properties to prevent secondary infection.'
        },
        'foods': ['oranges', 'leafy greens', 'fortified cereals', 'legumes', 'seafood']
    },
    'wound_healing': {
        'nutrients': ['Vitamin C', 'Zinc', 'Protein', 'Vitamin A', 'Iron'],
        'nutrient_explanations': {
            'Vitamin C': 'Absolutely essential for collagen synthesis - the primary protein in wound repair. Deficiency severely impairs healing.',
            'Zinc': 'Required for cell division, protein synthesis, and immune function - all critical for wound healing.',
            'Protein': 'Provides building blocks for new tissue. Wound healing increases protein requirements by 20-30%.',
            'Vitamin A': 'Stimulates epithelial growth and collagen synthesis. Enhances immune response at wound site.',
            'Iron': 'Carries oxygen to healing tissues. Anemia significantly delays wound healing.'
        },
        'foods': ['citrus fruits', 'meat', 'eggs', 'carrots', 'spinach']
    },
    'bloating': {
        'nutrients': ['Probiotics', 'Potassium', 'Ginger', 'Peppermint', 'Fennel'],
        'nutrient_explanations': {
            'Probiotics': 'Reduces gas-producing bacteria and improves gut motility to prevent trapped gas causing bloating.',
            'Potassium': 'Counteracts sodium-induced water retention. Helps regulate fluid balance to reduce bloating.',
            'Ginger': 'Stimulates digestive enzymes and speeds gastric emptying, preventing food from fermenting and causing gas.',
            'Peppermint': 'Relaxes intestinal muscles allowing trapped gas to pass. Natural antispasmodic for digestive tract.',
            'Fennel': 'Traditional carminative that relaxes intestinal muscles and reduces gas production.'
        },
        'foods': ['kefir', 'banana', 'ginger', 'peppermint', 'fennel seeds']
    },
    'constipation': {
        'nutrients': ['Fiber', 'Magnesium', 'Probiotics', 'Water', 'Vitamin C'],
        'nutrient_explanations': {
            'Fiber': 'Adds bulk to stool and stimulates intestinal movement. FDA recommends 25-30g daily for regularity.',
            'Magnesium': 'Natural laxative that draws water into intestines and relaxes bowel muscles for easier passage.',
            'Probiotics': 'Improves gut motility and stool consistency. Certain strains specifically help with constipation.',
            'Water': 'Essential for fiber to work properly. Dehydration is a leading cause of constipation.',
            'Vitamin C': 'High doses have natural laxative effect by drawing water into the colon.'
        },
        'foods': ['prunes', 'leafy greens', 'yogurt', 'chia seeds', 'kiwi']
    },
    'acid_reflux': {
        'nutrients': ['Fiber', 'Alkaline foods', 'Ginger', 'Probiotics', 'Melatonin'],
        'nutrient_explanations': {
            'Fiber': 'Absorbs stomach acid and promotes healthy digestion. High-fiber diets associated with less reflux.',
            'Alkaline foods': 'Help neutralize stomach acid and reduce symptoms. Vegetables and non-citrus fruits are naturally alkaline.',
            'Ginger': 'Natural anti-inflammatory that reduces acid production and speeds stomach emptying.',
            'Probiotics': 'Improve digestion to reduce pressure from fermentation that pushes acid upward.',
            'Melatonin': 'Strengthens lower esophageal sphincter and protects esophageal lining from acid damage.'
        },
        'foods': ['oatmeal', 'bananas', 'ginger', 'yogurt', 'almonds']
    },
    'nausea': {
        'nutrients': ['Ginger', 'Vitamin B6', 'Peppermint', 'Electrolytes', 'Bland carbs'],
        'nutrient_explanations': {
            'Ginger': 'FDA-recognized for pregnancy nausea. Blocks serotonin receptors in gut that trigger nausea signals.',
            'Vitamin B6': 'Particularly effective for pregnancy-related nausea. Involved in neurotransmitter synthesis affecting nausea.',
            'Peppermint': 'Relaxes stomach muscles and has anesthetic properties that calm nausea receptors.',
            'Electrolytes': 'Replace minerals lost through vomiting. Imbalance can worsen nausea symptoms.',
            'Bland carbs': 'Easy to digest and absorb stomach acid. Settle the stomach without triggering more nausea.'
        },
        'foods': ['ginger', 'bananas', 'peppermint', 'crackers', 'rice']
    },
    'digestive_issues': {
        'nutrients': ['Probiotics', 'Fiber', 'Ginger', 'Peppermint', 'Glutamine'],
        'nutrient_explanations': {
            'Probiotics': 'Restores healthy gut bacteria balance essential for proper digestion. FDA recognizes specific strains for digestive health.',
            'Fiber': 'Feeds beneficial gut bacteria and promotes regular bowel movements. Essential for gut motility.',
            'Ginger': 'Accelerates gastric emptying and reduces nausea. Has been used for digestive issues for thousands of years.',
            'Peppermint': 'Relaxes smooth muscle in the digestive tract, reducing cramping and bloating.',
            'Glutamine': 'Primary fuel source for intestinal cells. Helps maintain gut barrier integrity and repair.'
        },
        'foods': ['yogurt', 'whole grains', 'ginger', 'peppermint tea', 'bone broth']
    },
    'fatigue': {
        'nutrients': ['Iron', 'Vitamin B12', 'Vitamin D', 'Magnesium', 'CoQ10'],
        'nutrient_explanations': {
            'Iron': 'Carries oxygen in blood to all cells for energy production. Iron deficiency is the #1 cause of fatigue worldwide.',
            'Vitamin B12': 'Essential for red blood cell formation and nervous system function. Deficiency causes profound fatigue.',
            'Vitamin D': 'Low levels strongly associated with fatigue. Involved in mitochondrial function for cellular energy.',
            'Magnesium': 'Required for ATP (cellular energy) production. Deficiency impairs energy metabolism.',
            'CoQ10': 'Critical component of mitochondrial energy production. Levels decline with age and certain medications.'
        },
        'foods': ['red meat', 'eggs', 'fortified milk', 'spinach', 'organ meats']
    },
    'low_energy': {
        'nutrients': ['Complex Carbs', 'Iron', 'B Vitamins', 'Magnesium', 'Protein'],
        'nutrient_explanations': {
            'Complex Carbs': 'Provide steady glucose release for sustained energy without blood sugar spikes and crashes.',
            'Iron': 'Oxygen transport to muscles and brain. Even mild deficiency causes noticeable energy reduction.',
            'B Vitamins': 'Convert food into cellular energy. All B vitamins work together in energy metabolism.',
            'Magnesium': 'Involved in over 300 enzymatic reactions including energy production. Common deficiency.',
            'Protein': 'Stabilizes blood sugar and provides sustained energy. Essential for muscle energy.'
        },
        'foods': ['whole grains', 'lean meat', 'nuts', 'bananas', 'eggs']
    },
    'brain_fog': {
        'nutrients': ['Omega-3', 'B Vitamins', 'Vitamin D', 'Iron', 'Antioxidants'],
        'nutrient_explanations': {
            'Omega-3': 'DHA makes up 40% of brain cell membranes. Essential for neurotransmitter function and mental clarity.',
            'B Vitamins': 'B12 and folate critical for neurotransmitter synthesis. Deficiency directly causes cognitive impairment.',
            'Vitamin D': 'Receptors throughout brain. Low levels linked to cognitive decline and mental fog.',
            'Iron': 'Brain uses 20% of body\'s oxygen supply. Iron deficiency impairs cognitive function.',
            'Antioxidants': 'Protect brain cells from oxidative damage that impairs cognitive function.'
        },
        'foods': ['fatty fish', 'eggs', 'mushrooms', 'spinach', 'blueberries']
    },
    'anxiety': {
        'nutrients': ['Magnesium', 'Omega-3', 'B Vitamins', 'L-Theanine', 'Probiotics'],
        'nutrient_explanations': {
            'Magnesium': 'Regulates stress hormones and calms nervous system. Called "nature\'s relaxant" - deficiency worsens anxiety.',
            'Omega-3': 'Reduces inflammation linked to anxiety. EPA particularly effective for mood disorders.',
            'B Vitamins': 'Essential for neurotransmitter synthesis including serotonin and GABA. Deficiency increases anxiety.',
            'L-Theanine': 'Promotes alpha brain waves associated with calm alertness. Reduces anxiety without sedation.',
            'Probiotics': 'Gut-brain axis research shows gut bacteria influence anxiety. Specific strains reduce anxiety symptoms.'
        },
        'foods': ['dark chocolate', 'salmon', 'eggs', 'green tea', 'fermented foods']
    },
    'stress': {
        'nutrients': ['Magnesium', 'Vitamin C', 'B Vitamins', 'Adaptogens', 'Omega-3'],
        'nutrient_explanations': {
            'Magnesium': 'Depleted during stress. Calms nervous system and reduces cortisol levels.',
            'Vitamin C': 'Adrenal glands use large amounts during stress. Supports stress hormone production.',
            'B Vitamins': 'Rapidly depleted during stress. Essential for energy and nervous system function.',
            'Adaptogens': 'Herbs like ashwagandha help body adapt to stress. Reduce cortisol and improve resilience.',
            'Omega-3': 'Reduces stress-induced inflammation and supports healthy brain function under pressure.'
        },
        'foods': ['dark leafy greens', 'citrus', 'whole grains', 'ashwagandha', 'walnuts']
    },
    'depression': {
        'nutrients': ['Omega-3', 'Vitamin D', 'B Vitamins', 'Zinc', 'Probiotics'],
        'nutrient_explanations': {
            'Omega-3': 'EPA and DHA improve neurotransmitter function. Studies show comparable effects to antidepressants in mild cases.',
            'Vitamin D': 'Receptors throughout brain affect mood. Low levels strongly linked to depression.',
            'B Vitamins': 'B12 and folate essential for serotonin synthesis. Deficiency mimics depression symptoms.',
            'Zinc': 'Required for neurotransmitter function. Low zinc correlates with depression severity.',
            'Probiotics': 'Gut produces 90% of serotonin. Specific strains shown to improve mood.'
        },
        'foods': ['fatty fish', 'egg yolks', 'fortified cereals', 'nuts', 'yogurt']
    },
    'insomnia': {
        'nutrients': ['Magnesium', 'Melatonin', 'Tryptophan', 'Vitamin B6', 'Calcium'],
        'nutrient_explanations': {
            'Magnesium': 'Activates parasympathetic nervous system for relaxation. Regulates melatonin production.',
            'Melatonin': 'Body\'s natural sleep hormone. Found in tart cherries. Regulates sleep-wake cycle.',
            'Tryptophan': 'Amino acid precursor to serotonin and melatonin. Promotes natural sleepiness.',
            'Vitamin B6': 'Required to convert tryptophan to serotonin and melatonin. Supports sleep cycles.',
            'Calcium': 'Brain uses calcium to produce melatonin. Deficiency can cause sleep disturbances.'
        },
        'foods': ['almonds', 'tart cherries', 'turkey', 'bananas', 'warm milk']
    },
    'weak_immunity': {
        'nutrients': ['Vitamin C', 'Vitamin D', 'Zinc', 'Elderberry', 'Probiotics'],
        'nutrient_explanations': {
            'Vitamin C': 'Enhances immune cell function and antibody production. Reduces duration and severity of infections.',
            'Vitamin D': 'Activates immune cells and regulates immune response. Deficiency increases infection risk.',
            'Zinc': 'Required for immune cell development and function. Deficiency impairs both innate and adaptive immunity.',
            'Elderberry': 'Contains antioxidants and antiviral compounds. Studies show reduced cold and flu duration.',
            'Probiotics': '70% of immune system is in gut. Healthy microbiome essential for immune function.'
        },
        'foods': ['citrus', 'fortified milk', 'shellfish', 'elderberry', 'yogurt']
    },
    'cold_symptoms': {
        'nutrients': ['Vitamin C', 'Zinc', 'Elderberry', 'Honey', 'Ginger'],
        'nutrient_explanations': {
            'Vitamin C': 'Reduces cold duration by 8% in adults when taken regularly. Supports immune cell function.',
            'Zinc': 'Taken within 24 hours of symptoms, reduces cold duration by 33%. Interferes with viral replication.',
            'Elderberry': 'Antiviral properties reduce flu symptoms by average of 4 days in clinical studies.',
            'Honey': 'Natural cough suppressant as effective as OTC medications. Soothes sore throat.',
            'Ginger': 'Anti-inflammatory and antiviral properties. Helps with congestion and sore throat.'
        },
        'foods': ['oranges', 'oysters', 'elderberry syrup', 'raw honey', 'ginger tea']
    },
    'flu_symptoms': {
        'nutrients': ['Vitamin C', 'Vitamin D', 'Zinc', 'Protein', 'Fluids'],
        'nutrient_explanations': {
            'Vitamin C': 'Supports immune cell function during infection. May reduce symptom severity.',
            'Vitamin D': 'Produces antimicrobial peptides that fight viruses. Deficiency increases flu susceptibility.',
            'Zinc': 'Inhibits viral replication and boosts immune response. Most effective early in infection.',
            'Protein': 'Immune system requires extra protein during infection for antibody production.',
            'Fluids': 'Fever increases fluid needs. Hydration thins mucus and supports immune function.'
        },
        'foods': ['citrus fruits', 'fatty fish', 'pumpkin seeds', 'chicken soup', 'herbal tea']
    },
    'joint_pain': {
        'nutrients': ['Omega-3', 'Glucosamine', 'Vitamin D', 'Curcumin', 'Collagen'],
        'nutrient_explanations': {
            'Omega-3': 'Reduces joint inflammation and stiffness. Studies show decreased need for pain medication.',
            'Glucosamine': 'Building block for cartilage repair. May slow joint deterioration over time.',
            'Vitamin D': 'Deficiency linked to increased joint pain. Supports bone health and reduces inflammation.',
            'Curcumin': 'Reduces joint pain and swelling comparable to NSAIDs in some studies.',
            'Collagen': 'Main structural protein in joints. Supplementation supports cartilage health.'
        },
        'foods': ['salmon', 'shellfish', 'fortified milk', 'turmeric', 'bone broth']
    },
    'arthritis': {
        'nutrients': ['Omega-3', 'Vitamin D', 'Antioxidants', 'Curcumin', 'Ginger'],
        'nutrient_explanations': {
            'Omega-3': 'Reduces inflammatory cytokines that cause joint destruction. Arthritis Foundation recommends fish oil.',
            'Vitamin D': 'Regulates immune response in autoimmune arthritis. Low levels worsen symptoms.',
            'Antioxidants': 'Combat oxidative stress that damages joint tissue. Reduce inflammatory burden.',
            'Curcumin': 'Blocks inflammatory pathways. Studies show reduced joint swelling and pain.',
            'Ginger': 'Contains compounds similar to NSAIDs. Reduces joint pain with regular use.'
        },
        'foods': ['fatty fish', 'fortified foods', 'berries', 'turmeric', 'ginger']
    },
    'muscle_pain': {
        'nutrients': ['Magnesium', 'Potassium', 'Protein', 'Omega-3', 'Tart Cherry'],
        'nutrient_explanations': {
            'Magnesium': 'Relaxes muscles and prevents cramping. Deficiency causes muscle tension and pain.',
            'Potassium': 'Essential for muscle contraction and relaxation. Imbalance causes cramps and weakness.',
            'Protein': 'Provides amino acids for muscle repair. Inadequate protein delays recovery.',
            'Omega-3': 'Reduces delayed onset muscle soreness and inflammation after exercise.',
            'Tart Cherry': 'Contains anthocyanins that reduce muscle damage markers and speed recovery.'
        },
        'foods': ['bananas', 'spinach', 'lean meat', 'salmon', 'tart cherry juice']
    },
    'general_inflammation': {
        'nutrients': ['Omega-3', 'Vitamin C', 'Vitamin E', 'Curcumin', 'Quercetin'],
        'nutrient_explanations': {
            'Omega-3': 'Produces anti-inflammatory compounds (resolvins). Directly counters pro-inflammatory omega-6 effects.',
            'Vitamin C': 'Reduces inflammatory markers like C-reactive protein. Protects cells from inflammatory damage.',
            'Vitamin E': 'Interrupts inflammatory cascade by neutralizing free radicals that trigger inflammation.',
            'Curcumin': 'Inhibits NF-kB, the master switch for inflammation. As effective as some anti-inflammatory drugs.',
            'Quercetin': 'Stabilizes mast cells and inhibits inflammatory enzymes. Natural antihistamine properties.'
        },
        'foods': ['fish', 'berries', 'nuts', 'turmeric', 'onions']
    },
    'high_blood_pressure': {
        'nutrients': ['Potassium', 'Magnesium', 'Omega-3', 'Fiber', 'Nitrates'],
        'nutrient_explanations': {
            'Potassium': 'Counteracts sodium\'s blood pressure-raising effect. DASH diet emphasizes potassium for hypertension.',
            'Magnesium': 'Relaxes blood vessel walls. Low magnesium linked to hypertension.',
            'Omega-3': 'Reduces blood vessel inflammation and improves artery flexibility.',
            'Fiber': 'Associated with lower blood pressure. Helps maintain healthy weight.',
            'Nitrates': 'Convert to nitric oxide which dilates blood vessels. Beets can lower BP within hours.'
        },
        'foods': ['bananas', 'spinach', 'salmon', 'oats', 'beets']
    },
    'high_cholesterol': {
        'nutrients': ['Fiber', 'Omega-3', 'Plant Sterols', 'Niacin', 'Antioxidants'],
        'nutrient_explanations': {
            'Fiber': 'Soluble fiber binds cholesterol in gut preventing absorption. Oats can reduce LDL by 5-10%.',
            'Omega-3': 'Reduces triglycerides by 15-30%. Improves overall cholesterol profile.',
            'Plant Sterols': 'Block cholesterol absorption. FDA allows health claims for sterols and cholesterol.',
            'Niacin': 'Raises HDL (good cholesterol) more effectively than most medications.',
            'Antioxidants': 'Prevent LDL oxidation which is what makes cholesterol dangerous to arteries.'
        },
        'foods': ['oats', 'fatty fish', 'nuts', 'avocado', 'olive oil']
    },
    'heart_health': {
        'nutrients': ['Omega-3', 'Fiber', 'Potassium', 'Antioxidants', 'Magnesium'],
        'nutrient_explanations': {
            'Omega-3': 'Reduces irregular heartbeat, lowers triglycerides, slows plaque buildup. FDA-approved for heart health.',
            'Fiber': 'Reduces cholesterol and blood pressure. High-fiber diets reduce heart disease risk by 40%.',
            'Potassium': 'Regulates heartbeat and blood pressure. Essential for electrical activity of heart.',
            'Antioxidants': 'Prevent oxidative damage to heart and blood vessels. Reduce inflammation.',
            'Magnesium': 'Required for normal heart rhythm. Deficiency increases heart disease risk.'
        },
        'foods': ['salmon', 'whole grains', 'leafy greens', 'berries', 'dark chocolate']
    },
    'blood_sugar': {
        'nutrients': ['Fiber', 'Chromium', 'Magnesium', 'Cinnamon', 'Alpha-Lipoic Acid'],
        'nutrient_explanations': {
            'Fiber': 'Slows glucose absorption preventing blood sugar spikes. FDA recommends high fiber for diabetes prevention.',
            'Chromium': 'Enhances insulin function. Essential trace mineral for glucose metabolism.',
            'Magnesium': 'Involved in insulin production and glucose uptake. Deficiency increases diabetes risk.',
            'Cinnamon': 'Improves insulin sensitivity. Studies show reduced fasting blood sugar.',
            'Alpha-Lipoic Acid': 'Antioxidant that improves insulin sensitivity and reduces diabetic neuropathy symptoms.'
        },
        'foods': ['legumes', 'broccoli', 'nuts', 'cinnamon', 'spinach']
    },
    'diabetes_support': {
        'nutrients': ['Fiber', 'Chromium', 'Magnesium', 'Omega-3', 'Vitamin D'],
        'nutrient_explanations': {
            'Fiber': 'Reduces post-meal blood sugar spikes by 20-30%. Essential for diabetes management.',
            'Chromium': 'Enhances insulin receptor sensitivity. Helps cells respond to insulin properly.',
            'Magnesium': 'People with diabetes often deficient. Improves glucose control.',
            'Omega-3': 'Reduces inflammation that worsens insulin resistance. Protects heart health.',
            'Vitamin D': 'Improves insulin sensitivity and beta cell function. Low levels increase diabetes risk.'
        },
        'foods': ['beans', 'whole grains', 'leafy greens', 'fatty fish', 'fortified milk']
    },
    'weight_loss': {
        'nutrients': ['Protein', 'Fiber', 'Green Tea Extract', 'Omega-3', 'Probiotics'],
        'nutrient_explanations': {
            'Protein': 'Increases satiety hormones and boosts metabolism. Burns more calories during digestion.',
            'Fiber': 'Creates fullness with fewer calories. Slows digestion for sustained energy.',
            'Green Tea Extract': 'Contains EGCG which boosts metabolism and fat oxidation. Caffeine enhances effect.',
            'Omega-3': 'Improves fat metabolism and reduces inflammation that promotes weight gain.',
            'Probiotics': 'Certain strains associated with reduced weight gain and improved fat metabolism.'
        },
        'foods': ['lean protein', 'vegetables', 'green tea', 'salmon', 'yogurt']
    },
    'metabolism_boost': {
        'nutrients': ['Protein', 'Iron', 'B Vitamins', 'Green Tea', 'Capsaicin'],
        'nutrient_explanations': {
            'Protein': 'Has highest thermic effect of any macronutrient - burns 20-30% of calories during digestion.',
            'Iron': 'Required for thyroid hormone production which controls metabolism. Deficiency slows metabolism.',
            'B Vitamins': 'Essential for converting food to energy. Every step of metabolism requires B vitamins.',
            'Green Tea': 'EGCG and caffeine increase calorie burning by 4-5%. Enhances fat oxidation.',
            'Capsaicin': 'Compound in chili peppers temporarily boosts metabolism and increases fat burning.'
        },
        'foods': ['lean meat', 'spinach', 'eggs', 'green tea', 'chili peppers']
    },
    'hair_loss': {
        'nutrients': ['Biotin', 'Iron', 'Zinc', 'Protein', 'Vitamin D'],
        'nutrient_explanations': {
            'Biotin': 'Essential for keratin production - the protein that makes up hair. Deficiency causes hair loss.',
            'Iron': 'Hair follicles require iron for growth. Iron deficiency is the most common cause of hair loss in women.',
            'Zinc': 'Crucial for hair tissue growth and repair. Deficiency causes hair loss and slow growth.',
            'Protein': 'Hair is 95% protein (keratin). Inadequate protein causes weak, brittle, thinning hair.',
            'Vitamin D': 'Stimulates hair follicles. Low levels associated with alopecia and hair thinning.'
        },
        'foods': ['eggs', 'spinach', 'pumpkin seeds', 'lean meat', 'fatty fish']
    },
    'eye_health': {
        'nutrients': ['Vitamin A', 'Lutein', 'Zeaxanthin', 'Omega-3', 'Vitamin C'],
        'nutrient_explanations': {
            'Vitamin A': 'Essential for light-detecting cells in retina. Deficiency is leading cause of preventable blindness.',
            'Lutein': 'Filters harmful blue light and protects macula. Reduces macular degeneration risk by 43%.',
            'Zeaxanthin': 'Works with lutein in the macula. Antioxidant protection for central vision.',
            'Omega-3': 'DHA is a major structural component of retina. Reduces dry eye and macular degeneration risk.',
            'Vitamin C': 'High concentration in eye fluid. Protects against cataracts and age-related damage.'
        },
        'foods': ['carrots', 'spinach', 'eggs', 'salmon', 'citrus fruits']
    },
    'bone_health': {
        'nutrients': ['Calcium', 'Vitamin D', 'Vitamin K', 'Magnesium', 'Phosphorus'],
        'nutrient_explanations': {
            'Calcium': '99% of body\'s calcium is in bones. FDA-recognized essential nutrient for bone health.',
            'Vitamin D': 'Required for calcium absorption. Without adequate D, only 10-15% of calcium is absorbed.',
            'Vitamin K': 'Activates osteocalcin protein that binds calcium to bones. K2 form most effective.',
            'Magnesium': '60% stored in bones. Required for vitamin D activation and bone cell function.',
            'Phosphorus': 'Works with calcium to form bone mineral matrix. Must be balanced with calcium.'
        },
        'foods': ['dairy', 'fortified milk', 'leafy greens', 'nuts', 'fish']
    },
    'allergies': {
        'nutrients': ['Quercetin', 'Vitamin C', 'Probiotics', 'Omega-3', 'Bromelain'],
        'nutrient_explanations': {
            'Quercetin': 'Natural antihistamine that stabilizes mast cells. Prevents histamine release causing symptoms.',
            'Vitamin C': 'Natural antihistamine and immune modulator. Reduces allergy symptom severity.',
            'Probiotics': 'Regulate immune response to allergens. Reduce allergic inflammation.',
            'Omega-3': 'Reduces inflammatory response to allergens. Balances pro-inflammatory omega-6.',
            'Bromelain': 'Enzyme that reduces nasal swelling and thins mucus. Enhances quercetin absorption.'
        },
        'foods': ['onions', 'citrus', 'yogurt', 'fatty fish', 'pineapple']
    },
    'headache': {
        'nutrients': ['Magnesium', 'Riboflavin (B2)', 'CoQ10', 'Omega-3', 'Ginger'],
        'nutrient_explanations': {
            'Magnesium': 'Deficiency is common in headache sufferers. Relaxes blood vessels and muscles.',
            'Riboflavin (B2)': 'High-dose B2 reduces headache frequency by 50% in studies.',
            'CoQ10': 'Improves cellular energy in brain. Studies show reduced headache days.',
            'Omega-3': 'Reduces inflammation that contributes to headaches. May reduce frequency.',
            'Ginger': 'As effective as sumatriptan for migraine relief in some studies.'
        },
        'foods': ['spinach', 'almonds', 'organ meats', 'fatty fish', 'ginger']
    },
    'migraine': {
        'nutrients': ['Magnesium', 'Riboflavin', 'CoQ10', 'Feverfew', 'Omega-3'],
        'nutrient_explanations': {
            'Magnesium': 'American Migraine Foundation recommends 400-500mg daily for prevention.',
            'Riboflavin': '400mg daily reduces migraine frequency by 50%. Works within 3 months.',
            'CoQ10': 'Reduces migraine days by 50% in clinical trials. Improves brain energy.',
            'Feverfew': 'Traditional migraine herb. Inhibits inflammatory compounds that trigger migraines.',
            'Omega-3': 'High-dose omega-3 reduces migraine frequency and severity.'
        },
        'foods': ['dark leafy greens', 'eggs', 'sardines', 'feverfew tea', 'salmon']
    },
}


def _get_nutrient_recommendations(condition_type):
    ct = condition_type.lower().replace(' ', '_').replace('-', '_')
    if ct in NUTRIENT_DB:
        return NUTRIENT_DB[ct]
    for key in NUTRIENT_DB:
        if key in ct or ct in key:
            return NUTRIENT_DB[key]
    return NUTRIENT_DB.get('general_inflammation', {'nutrients': ['Omega-3', 'Vitamin C'], 'foods': ['fish', 'berries']})


# ======================== FDA FOOD SEARCH ========================

def _search_fda_foods(nutrient_name, limit=5):
    try:
        params = urlencode({'api_key': _get_secret('FDA_API_KEY'), 'query': nutrient_name, 'pageSize': limit, 'dataType': 'Foundation,SR Legacy'})
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?{params}"
        data = _http_get(url)
        foods = []
        for food in data.get('foods', []):
            nutrients = [{'name': n.get('nutrientName'), 'amount': n.get('value'), 'unit': n.get('unitName')}
                         for n in food.get('foodNutrients', [])[:10]]
            foods.append({'fdcId': food.get('fdcId'), 'description': food.get('description'), 'nutrients': nutrients})
        return foods
    except Exception:
        return []


def _find_foods_for_condition(nutrients):
    all_foods = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_nutrient = {executor.submit(_search_fda_foods, n, 5): n for n in nutrients}
        for future in future_to_nutrient:
            nutrient = future_to_nutrient[future]
            try:
                foods = future.result(timeout=15)
                for food in foods:
                    fid = food['fdcId']
                    if fid not in all_foods:
                        all_foods[fid] = food
                        all_foods[fid]['beneficial_for'] = [nutrient]
                    else:
                        all_foods[fid]['beneficial_for'].append(nutrient)
            except Exception:
                continue
    return sorted(all_foods.values(), key=lambda x: len(x.get('beneficial_for', [])), reverse=True)[:10]


# ======================== PREFERENCE FILTERING ========================

ALLERGEN_KEYWORDS = {
    'peanuts': ['peanut', 'groundnut'],
    'tree_nuts': ['almond', 'walnut', 'cashew', 'pecan', 'pistachio', 'hazelnut', 'macadamia'],
    'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'lactose', 'whey', 'casein'],
    'eggs': ['egg', 'albumin'],
    'soy': ['soy', 'soya', 'tofu', 'tempeh', 'edamame'],
    'gluten': ['wheat', 'barley', 'rye', 'bread', 'pasta', 'flour', 'oat'],
    'fish': ['fish', 'salmon', 'tuna', 'cod', 'tilapia', 'sardine'],
    'shellfish': ['shrimp', 'crab', 'lobster', 'clam', 'mussel', 'oyster', 'scallop'],
}

DIET_RESTRICTIONS = {
    'vegetarian': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage', 'fish', 'seafood', 'salmon', 'tuna'],
    'vegan': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'fish', 'seafood', 'salmon', 'tuna', 'milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg', 'honey', 'dairy'],
    'pescatarian': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage'],
    'keto': ['bread', 'pasta', 'rice', 'potato', 'sugar', 'corn', 'cereal', 'oat', 'wheat'],
    'paleo': ['bread', 'pasta', 'rice', 'cereal', 'oat', 'wheat', 'dairy', 'milk', 'cheese', 'legume', 'bean', 'peanut', 'soy'],
}


def _build_exclude_keywords(allergies, diet_type):
    exclude = set()
    for allergy in (allergies or []):
        al = allergy.lower()
        if al in ALLERGEN_KEYWORDS:
            exclude.update(ALLERGEN_KEYWORDS[al])
        else:
            exclude.add(al)
    if diet_type and diet_type in DIET_RESTRICTIONS:
        exclude.update(DIET_RESTRICTIONS[diet_type])
    return exclude


def _filter_foods(foods, allergies, diet_type):
    exclude = _build_exclude_keywords(allergies, diet_type)
    if not exclude:
        return foods
    return [f for f in foods if not any(kw in f.get('description', '').lower() for kw in exclude)]


def _filter_recipes(recipes, allergies, diet_type):
    exclude = _build_exclude_keywords(allergies, diet_type)
    if not exclude:
        return recipes[:5]
    filtered = []
    for r in recipes:
        text = r.get('title', '').lower()
        ings = r.get('ingredients', [])
        if isinstance(ings, list):
            text += ' ' + ' '.join(str(i).lower() for i in ings)
        if not any(kw in text for kw in exclude):
            filtered.append(r)
    return filtered[:5]


# ======================== AI FOOD CLEANUP ========================

def _cleanup_foods_with_ai(foods, condition_name):
    if not foods:
        return []
    descs = [f.get('description', '') for f in foods]
    prompt = f"""Clean up these FDA food names into simple WHOLE FOOD names.
Keep names as simple single ingredients (e.g., "Spinach", "Salmon", "Almonds").
Also provide a brief tip about each food for {condition_name} and an image search term.

Foods: {chr(10).join([f'{i+1}. {d}' for i, d in enumerate(descs)])}

Return JSON array:
[{{"displayName": "Spinach", "imageSearchTerm": "fresh spinach", "tip": "Rich in iron"}}]

Return ONLY the JSON array."""

    try:
        resp = _http_post('https://api.openai.com/v1/chat/completions', {
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': 'You are a nutrition assistant. Return valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 800, 'temperature': 0.7
        }, {'Content-Type': 'application/json', 'Authorization': f'Bearer {_get_secret("OPENAI_API_KEY")}'})

        text = resp['choices'][0]['message']['content'].strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
            text = text.strip()
        cleaned = json.loads(text)
    except Exception:
        cleaned = [{'displayName': _simple_cleanup(f.get('description', '')), 'imageSearchTerm': '', 'tip': ''} for f in foods]

    result = []
    for i, food in enumerate(foods):
        ai = cleaned[i] if i < len(cleaned) else {}
        dn = ai.get('displayName', _simple_cleanup(food.get('description', '')))
        result.append({
            'name': food.get('description', ''),
            'displayName': dn,
            'imageSearchTerm': ai.get('imageSearchTerm', dn.lower()),
            'tip': ai.get('tip', ''),
            'fdcId': food.get('fdcId', ''),
            'keyNutrients': food.get('nutrients', [])[:3],
            'beneficialFor': food.get('beneficial_for', [])
        })
    return result


def _simple_cleanup(name):
    if not name:
        return 'Food'
    for c in [', raw', ', fresh', ', cooked', ', boiled', ', NFS', ', NS as to form', ', mature seeds']:
        name = name.replace(c, '')
    return name.strip().title()


# ======================== RECIPE SEARCH (TheMealDB) ========================

def _fetch_recipes_for_term(term):
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={quote(term)}"
        data = _http_get(url, timeout=10)
        results = []
        for meal in (data.get('meals') or [])[:3]:
            ingredients = []
            for j in range(1, 21):
                ing = meal.get(f'strIngredient{j}', '')
                if ing and ing.strip():
                    measure = meal.get(f'strMeasure{j}', '')
                    ingredients.append(f"{measure} {ing}".strip())
            results.append({
                'id': meal.get('idMeal', ''),
                'title': meal.get('strMeal', ''),
                'image': meal.get('strMealThumb', ''),
                'readyInMinutes': 30,
                'servings': 4,
                'summary': (meal.get('strInstructions') or '')[:200],
                'instructions': [s for s in (meal.get('strInstructions') or '').split('\r\n') if s.strip()],
                'ingredients': ingredients,
                'nutrition': {},
                'healthScore': 0,
                'source': 'TheMealDB',
                'sourceUrl': meal.get('strSource', '')
            })
        return results
    except Exception:
        return []


def _search_recipes(nutrients, number=10):
    search_terms_map = {
        'Omega-3': 'salmon', 'Vitamin C': 'lemon', 'Iron': 'beef', 'Zinc': 'chicken',
        'Vitamin A': 'carrot', 'Fiber': 'oatmeal', 'Magnesium': 'spinach',
        'Probiotics': 'yogurt', 'Vitamin D': 'fish', 'Calcium': 'milk',
        'Potassium': 'banana', 'Vitamin E': 'almond', 'Protein': 'chicken',
    }
    terms = []
    searched = set()
    for nutrient in nutrients[:3]:
        term = search_terms_map.get(nutrient, nutrient.lower().split()[0])
        if term not in searched:
            searched.add(term)
            terms.append(term)

    recipes = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(_fetch_recipes_for_term, t) for t in terms]
        for future in futures:
            try:
                recipes.extend(future.result(timeout=15))
            except Exception:
                continue
    return recipes[:number]


# ======================== FOOD IMAGES ========================

def _get_food_image(food_name, size='medium'):
    if not _get_secret('PEXELS_API_KEY') or not food_name:
        return ''
    for q in [food_name, f"{food_name} food", f"fresh {food_name}"]:
        try:
            url = f"https://api.pexels.com/v1/search?query={quote(q)}&per_page=3&orientation=square"
            data = _http_get(url, headers={'Authorization': _get_secret('PEXELS_API_KEY')}, timeout=8)
            photos = data.get('photos', [])
            if photos:
                return photos[0]['src'].get(size, photos[0]['src'].get('medium', ''))
        except Exception:
            continue
    return ''


# ======================== MAIN HANDLER ========================

def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})
        if isinstance(body, str):
            body = json.loads(body)

        image_base64 = body.get('image_base64')
        text_description = body.get('text_description')
        user_concerns = body.get('user_concerns')
        allergies = [a.lower().strip() for a in (body.get('allergies') or [])]
        diet_type = (body.get('diet_type') or '').lower().strip()

        if not image_base64 and not text_description:
            return respond(400, {'error': 'Either image_base64 or text_description is required'})

        # Step 1: Analyze condition
        condition = _analyze_condition(image_base64, text_description, user_concerns)

        # Step 2: Get nutrient recommendations
        nutrient_info = _get_nutrient_recommendations(condition['condition_type'])

        # Step 3: Run FDA search and recipe search concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            fda_future = executor.submit(_find_foods_for_condition, nutrient_info['nutrients'])
            recipes_future = executor.submit(_search_recipes, nutrient_info['nutrients'], 10)

            recommended_foods = fda_future.result(timeout=30)
            recipes = recipes_future.result(timeout=30)

        # Step 4: Filter by preferences
        recommended_foods = _filter_foods(recommended_foods, allergies, diet_type)
        recipes = _filter_recipes(recipes, allergies, diet_type)

        # Step 5: Clean up food names with AI
        cleaned_foods = _cleanup_foods_with_ai(recommended_foods[:8], condition['condition_name'])

        # Step 6: Build response
        nutrients = ', '.join(nutrient_info['nutrients'][:4])
        foods_list = ', '.join(nutrient_info['foods'][:4])

        response = {
            'condition': {
                'name': condition['condition_name'],
                'type': condition['condition_type'],
                'explanation': condition['explanation'],
                'severity': condition.get('severity', 'mild')
            },
            'remedy': {
                'recommendedNutrients': nutrient_info['nutrients'],
                'nutrientExplanations': nutrient_info.get('nutrient_explanations', {}),
                'foodCategories': nutrient_info['foods'],
                'specificFoods': cleaned_foods,
                'recipes': [{
                    'id': r.get('id', ''), 'title': r.get('title', ''),
                    'image': r.get('image', ''), 'readyInMinutes': r.get('readyInMinutes', 30),
                    'servings': r.get('servings', 4), 'summary': r.get('summary', ''),
                    'instructions': r.get('instructions', []),
                    'ingredients': r.get('ingredients', []),
                    'nutrition': r.get('nutrition', {}),
                    'healthScore': r.get('healthScore', 0),
                    'source': r.get('source', 'TheMealDB'),
                    'sourceUrl': r.get('sourceUrl', '')
                } for r in recipes[:5]],
                'explanation': f"Based on research, {nutrients} are beneficial for {condition['condition_name']}. Top food sources include {foods_list}."
            },
            'sources': {
                'nutritionData': ['FDA FoodData Central', 'NIH Office of Dietary Supplements'],
                'recipeData': 'TheMealDB',
                'citations': [
                    {'name': 'FDA FoodData Central', 'url': 'https://fdc.nal.usda.gov/', 'description': 'USDA food composition database'},
                    {'name': 'NIH Office of Dietary Supplements', 'url': 'https://ods.od.nih.gov/', 'description': 'NIH dietary supplement fact sheets'},
                    {'name': 'PubMed', 'url': 'https://pubmed.ncbi.nlm.nih.gov/', 'description': 'Peer-reviewed nutrition research'}
                ]
            },
            'disclaimer': 'This information is for educational purposes only. It is not a substitute for professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment.'
        }

        return respond(200, response)

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
