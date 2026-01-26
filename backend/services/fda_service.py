import requests
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class FDAService:
    def __init__(self):
        self.api_key = os.getenv('FDA_API_KEY', 'oG08t7cdtgaNiUzlpyIGFi0eIbPdAbCgYknAMcfe')
        self.base_url = "https://api.nal.usda.gov/fdc/v1"

    def search_foods_by_nutrient(self, nutrient_name: str, limit: int = 10) -> List[Dict]:
        """Search for foods rich in a specific nutrient"""
        try:
            search_url = f"{self.base_url}/foods/search"
            params = {
                'api_key': self.api_key,
                'query': nutrient_name,
                'pageSize': limit,
                'dataType': ['Foundation', 'SR Legacy']
            }

            response = requests.get(search_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            foods = []

            if 'foods' in data:
                for food in data['foods']:
                    foods.append({
                        'fdcId': food.get('fdcId'),
                        'description': food.get('description'),
                        'dataType': food.get('dataType'),
                        'nutrients': self._extract_nutrients(food.get('foodNutrients', []))
                    })

            return foods
        except Exception as e:
            print(f"Error searching FDA database: {str(e)}")
            return []

    def get_food_details(self, fdc_id: int) -> Optional[Dict]:
        """Get detailed information about a specific food"""
        try:
            url = f"{self.base_url}/food/{fdc_id}"
            params = {'api_key': self.api_key}

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            print(f"Error getting food details: {str(e)}")
            return None

    def find_foods_for_condition(self, condition: str, beneficial_nutrients: List[str]) -> List[Dict]:
        """Find foods that contain beneficial nutrients for a condition"""
        all_foods = {}

        for nutrient in beneficial_nutrients:
            foods = self.search_foods_by_nutrient(nutrient, limit=5)
            for food in foods:
                fdc_id = food['fdcId']
                if fdc_id not in all_foods:
                    all_foods[fdc_id] = food
                    all_foods[fdc_id]['beneficial_for'] = [nutrient]
                else:
                    all_foods[fdc_id]['beneficial_for'].append(nutrient)

        sorted_foods = sorted(
            all_foods.values(),
            key=lambda x: len(x.get('beneficial_for', [])),
            reverse=True
        )

        return sorted_foods[:10]

    def _extract_nutrients(self, food_nutrients: List[Dict]) -> List[Dict]:
        """Extract key nutrients from food nutrient data"""
        nutrients = []
        for nutrient in food_nutrients[:10]:
            nutrients.append({
                'name': nutrient.get('nutrientName'),
                'amount': nutrient.get('value'),
                'unit': nutrient.get('unitName')
            })
        return nutrients

    def get_nutrient_recommendations(self, condition: str) -> Dict[str, any]:
        """Get nutrient recommendations for health conditions - comprehensive knowledge base with FDA-backed explanations"""

        # Comprehensive condition-to-nutrient mapping with healing explanations based on FDA/NIH research
        recommendations = {
            # Skin Conditions
            'skin_inflammation': {
                'nutrients': ['Vitamin E', 'Vitamin C', 'Omega-3', 'Zinc', 'Selenium'],
                'nutrient_explanations': {
                    'Vitamin E': 'Protects skin cell membranes from oxidative damage and reduces inflammatory responses. FDA recognizes it as essential for skin barrier function.',
                    'Vitamin C': 'Essential for collagen synthesis which repairs damaged skin tissue. Also acts as an antioxidant to neutralize inflammation-causing free radicals.',
                    'Omega-3': 'Reduces production of inflammatory compounds (prostaglandins and leukotrienes) that cause skin redness and swelling.',
                    'Zinc': 'Accelerates wound healing and regulates immune responses that contribute to inflammation. Deficiency is linked to skin disorders.',
                    'Selenium': 'Works synergistically with Vitamin E to protect skin cells from oxidative stress and UV damage.'
                },
                'foods': ['almonds', 'citrus fruits', 'salmon', 'pumpkin seeds', 'brazil nuts'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            },
            'acne': {
                'nutrients': ['Zinc', 'Vitamin A', 'Omega-3', 'Vitamin E', 'Probiotics'],
                'nutrient_explanations': {
                    'Zinc': 'Reduces sebum production and has antimicrobial properties against acne-causing bacteria. Studies show zinc deficiency worsens acne.',
                    'Vitamin A': 'Regulates skin cell turnover, preventing pores from becoming clogged. The basis for prescription retinoid treatments.',
                    'Omega-3': 'Reduces inflammatory markers that cause acne lesions to become red and swollen. Balances omega-6 fatty acids that promote inflammation.',
                    'Vitamin E': 'Protects skin from oxidative damage and helps regulate sebum production to prevent clogged pores.',
                    'Probiotics': 'Supports gut-skin axis health. Research shows gut microbiome imbalance is linked to acne severity.'
                },
                'foods': ['pumpkin seeds', 'sweet potato', 'salmon', 'almonds', 'yogurt'],
                'sources': ['American Academy of Dermatology', 'NIH Office of Dietary Supplements']
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
                'foods': ['avocado', 'walnuts', 'sweet potato', 'eggs', 'bell peppers'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
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
                'foods': ['fatty fish', 'fortified milk', 'kefir', 'sunflower seeds', 'oysters'],
                'sources': ['National Eczema Association', 'NIH Office of Dietary Supplements']
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
                'foods': ['mackerel', 'sardines', 'brazil nuts', 'carrots', 'beef'],
                'sources': ['National Psoriasis Foundation', 'NIH Office of Dietary Supplements']
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
                'foods': ['berries', 'nuts', 'onions', 'fish', 'legumes'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
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
                'foods': ['citrus fruits', 'carrots', 'spinach', 'beans', 'lean meat'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
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
                'foods': ['oranges', 'leafy greens', 'fortified cereals', 'legumes', 'seafood'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            },
            'wound_healing': {
                'nutrients': ['Vitamin C', 'Zinc', 'Protein', 'Vitamin A', 'Iron'],
                'nutrient_explanations': {
                    'Vitamin C': 'Absolutely essential for collagen synthesis - the primary protein in wound repair. Deficiency severely impairs healing.',
                    'Zinc': 'Required for cell division, protein synthesis, and immune function - all critical for wound healing. Second only to Vitamin C.',
                    'Protein': 'Provides building blocks for new tissue. Wound healing increases protein requirements by 20-30%.',
                    'Vitamin A': 'Stimulates epithelial growth and collagen synthesis. Enhances immune response at wound site.',
                    'Iron': 'Carries oxygen to healing tissues. Anemia significantly delays wound healing.'
                },
                'foods': ['citrus fruits', 'meat', 'eggs', 'carrots', 'spinach'],
                'sources': ['NIH Office of Dietary Supplements', 'World Health Organization']
            },

            # Digestive Issues
            'digestive_issues': {
                'nutrients': ['Probiotics', 'Fiber', 'Ginger', 'Peppermint', 'Glutamine'],
                'nutrient_explanations': {
                    'Probiotics': 'Restores healthy gut bacteria balance essential for proper digestion. FDA recognizes specific strains for digestive health.',
                    'Fiber': 'Feeds beneficial gut bacteria and promotes regular bowel movements. Essential for gut motility.',
                    'Ginger': 'Accelerates gastric emptying and reduces nausea. Has been used for digestive issues for thousands of years.',
                    'Peppermint': 'Relaxes smooth muscle in the digestive tract, reducing cramping and bloating.',
                    'Glutamine': 'Primary fuel source for intestinal cells. Helps maintain gut barrier integrity and repair.'
                },
                'foods': ['yogurt', 'whole grains', 'ginger', 'peppermint tea', 'bone broth'],
                'sources': ['American Gastroenterological Association', 'NIH NCCIH']
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
                'foods': ['kefir', 'banana', 'ginger', 'peppermint', 'fennel seeds'],
                'sources': ['American College of Gastroenterology', 'NIH NCCIH']
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
                'foods': ['prunes', 'leafy greens', 'yogurt', 'chia seeds', 'kiwi'],
                'sources': ['NIH NIDDK', 'American Gastroenterological Association']
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
                'foods': ['oatmeal', 'bananas', 'ginger', 'yogurt', 'almonds'],
                'sources': ['American Gastroenterological Association', 'NIH NIDDK']
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
                'foods': ['ginger', 'bananas', 'peppermint', 'crackers', 'rice'],
                'sources': ['NIH NCCIH', 'American College of Gastroenterology']
            },

            # Energy and Fatigue
            'fatigue': {
                'nutrients': ['Iron', 'Vitamin B12', 'Vitamin D', 'Magnesium', 'CoQ10'],
                'nutrient_explanations': {
                    'Iron': 'Carries oxygen in blood to all cells for energy production. Iron deficiency is the #1 cause of fatigue worldwide.',
                    'Vitamin B12': 'Essential for red blood cell formation and nervous system function. Deficiency causes profound fatigue.',
                    'Vitamin D': 'Low levels strongly associated with fatigue. Involved in mitochondrial function for cellular energy.',
                    'Magnesium': 'Required for ATP (cellular energy) production. Deficiency impairs energy metabolism.',
                    'CoQ10': 'Critical component of mitochondrial energy production. Levels decline with age and certain medications.'
                },
                'foods': ['red meat', 'eggs', 'fortified milk', 'spinach', 'organ meats'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
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
                'foods': ['whole grains', 'lean meat', 'nuts', 'bananas', 'eggs'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
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
                'foods': ['fatty fish', 'eggs', 'mushrooms', 'spinach', 'blueberries'],
                'sources': ['NIH Office of Dietary Supplements', 'Alzheimers Association']
            },

            # Immune System
            'weak_immunity': {
                'nutrients': ['Vitamin C', 'Vitamin D', 'Zinc', 'Elderberry', 'Probiotics'],
                'nutrient_explanations': {
                    'Vitamin C': 'Enhances immune cell function and antibody production. Reduces duration and severity of infections.',
                    'Vitamin D': 'Activates immune cells and regulates immune response. Deficiency increases infection risk.',
                    'Zinc': 'Required for immune cell development and function. Deficiency impairs both innate and adaptive immunity.',
                    'Elderberry': 'Contains antioxidants and antiviral compounds. Studies show reduced cold and flu duration.',
                    'Probiotics': '70% of immune system is in gut. Healthy microbiome essential for immune function.'
                },
                'foods': ['citrus', 'fortified milk', 'shellfish', 'elderberry', 'yogurt'],
                'sources': ['NIH Office of Dietary Supplements', 'CDC']
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
                'foods': ['oranges', 'oysters', 'elderberry syrup', 'raw honey', 'ginger tea'],
                'sources': ['NIH NCCIH', 'Cochrane Reviews']
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
                'foods': ['citrus fruits', 'fatty fish', 'pumpkin seeds', 'chicken soup', 'herbal tea'],
                'sources': ['NIH Office of Dietary Supplements', 'CDC']
            },

            # Inflammation
            'general_inflammation': {
                'nutrients': ['Omega-3', 'Vitamin C', 'Vitamin E', 'Curcumin', 'Quercetin'],
                'nutrient_explanations': {
                    'Omega-3': 'Produces anti-inflammatory compounds (resolvins). Directly counters pro-inflammatory omega-6 effects.',
                    'Vitamin C': 'Reduces inflammatory markers like C-reactive protein. Protects cells from inflammatory damage.',
                    'Vitamin E': 'Interrupts inflammatory cascade by neutralizing free radicals that trigger inflammation.',
                    'Curcumin': 'Inhibits NF-kB, the master switch for inflammation. As effective as some anti-inflammatory drugs.',
                    'Quercetin': 'Stabilizes mast cells and inhibits inflammatory enzymes. Natural antihistamine properties.'
                },
                'foods': ['fish', 'berries', 'nuts', 'turmeric', 'onions'],
                'sources': ['NIH NCCIH', 'Arthritis Foundation']
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
                'foods': ['salmon', 'shellfish', 'fortified milk', 'turmeric', 'bone broth'],
                'sources': ['Arthritis Foundation', 'NIH NCCIH']
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
                'foods': ['fatty fish', 'fortified foods', 'berries', 'turmeric', 'ginger'],
                'sources': ['Arthritis Foundation', 'NIH NCCIH']
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
                'foods': ['bananas', 'spinach', 'lean meat', 'salmon', 'tart cherry juice'],
                'sources': ['NIH Office of Dietary Supplements', 'American College of Sports Medicine']
            },

            # Mental Health
            'anxiety': {
                'nutrients': ['Magnesium', 'Omega-3', 'B Vitamins', 'L-Theanine', 'Probiotics'],
                'nutrient_explanations': {
                    'Magnesium': 'Regulates stress hormones and calms nervous system. Called "nature\'s relaxant" - deficiency worsens anxiety.',
                    'Omega-3': 'Reduces inflammation linked to anxiety. EPA particularly effective for mood disorders.',
                    'B Vitamins': 'Essential for neurotransmitter synthesis including serotonin and GABA. Deficiency increases anxiety.',
                    'L-Theanine': 'Promotes alpha brain waves associated with calm alertness. Reduces anxiety without sedation.',
                    'Probiotics': 'Gut-brain axis research shows gut bacteria influence anxiety. Specific strains reduce anxiety symptoms.'
                },
                'foods': ['dark chocolate', 'salmon', 'eggs', 'green tea', 'fermented foods'],
                'sources': ['NIH NIMH', 'NIH Office of Dietary Supplements']
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
                'foods': ['dark leafy greens', 'citrus', 'whole grains', 'ashwagandha', 'walnuts'],
                'sources': ['NIH Office of Dietary Supplements', 'American Psychological Association']
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
                'foods': ['fatty fish', 'egg yolks', 'fortified cereals', 'nuts', 'yogurt'],
                'sources': ['NIH NIMH', 'NIH Office of Dietary Supplements']
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
                'foods': ['almonds', 'tart cherries', 'turkey', 'bananas', 'warm milk'],
                'sources': ['NIH Office of Dietary Supplements', 'Sleep Foundation']
            },

            # Heart Health
            'high_blood_pressure': {
                'nutrients': ['Potassium', 'Magnesium', 'Omega-3', 'Fiber', 'Nitrates'],
                'nutrient_explanations': {
                    'Potassium': 'Counteracts sodium\'s blood pressure-raising effect. DASH diet emphasizes potassium for hypertension.',
                    'Magnesium': 'Relaxes blood vessel walls. Low magnesium linked to hypertension.',
                    'Omega-3': 'Reduces blood vessel inflammation and improves artery flexibility.',
                    'Fiber': 'Associated with lower blood pressure. Helps maintain healthy weight.',
                    'Nitrates': 'Convert to nitric oxide which dilates blood vessels. Beets can lower BP within hours.'
                },
                'foods': ['bananas', 'spinach', 'salmon', 'oats', 'beets'],
                'sources': ['American Heart Association', 'NIH NHLBI']
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
                'foods': ['oats', 'fatty fish', 'nuts', 'avocado', 'olive oil'],
                'sources': ['American Heart Association', 'NIH NHLBI']
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
                'foods': ['salmon', 'whole grains', 'leafy greens', 'berries', 'dark chocolate'],
                'sources': ['American Heart Association', 'NIH NHLBI']
            },

            # Blood Sugar
            'blood_sugar': {
                'nutrients': ['Fiber', 'Chromium', 'Magnesium', 'Cinnamon', 'Alpha-Lipoic Acid'],
                'nutrient_explanations': {
                    'Fiber': 'Slows glucose absorption preventing blood sugar spikes. FDA recommends high fiber for diabetes prevention.',
                    'Chromium': 'Enhances insulin function. Essential trace mineral for glucose metabolism.',
                    'Magnesium': 'Involved in insulin production and glucose uptake. Deficiency increases diabetes risk.',
                    'Cinnamon': 'Improves insulin sensitivity. Studies show reduced fasting blood sugar.',
                    'Alpha-Lipoic Acid': 'Antioxidant that improves insulin sensitivity and reduces diabetic neuropathy symptoms.'
                },
                'foods': ['legumes', 'broccoli', 'nuts', 'cinnamon', 'spinach'],
                'sources': ['American Diabetes Association', 'NIH Office of Dietary Supplements']
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
                'foods': ['beans', 'whole grains', 'leafy greens', 'fatty fish', 'fortified milk'],
                'sources': ['American Diabetes Association', 'NIH NIDDK']
            },

            # Weight Management
            'weight_loss': {
                'nutrients': ['Protein', 'Fiber', 'Green Tea Extract', 'Omega-3', 'Probiotics'],
                'nutrient_explanations': {
                    'Protein': 'Increases satiety hormones and boosts metabolism. Burns more calories during digestion.',
                    'Fiber': 'Creates fullness with fewer calories. Slows digestion for sustained energy.',
                    'Green Tea Extract': 'Contains EGCG which boosts metabolism and fat oxidation. Caffeine enhances effect.',
                    'Omega-3': 'Improves fat metabolism and reduces inflammation that promotes weight gain.',
                    'Probiotics': 'Certain strains associated with reduced weight gain and improved fat metabolism.'
                },
                'foods': ['lean protein', 'vegetables', 'green tea', 'salmon', 'yogurt'],
                'sources': ['NIH NIDDK', 'FDA FoodData Central']
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
                'foods': ['lean meat', 'spinach', 'eggs', 'green tea', 'chili peppers'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            },

            # Hair and Nails
            'hair_loss': {
                'nutrients': ['Biotin', 'Iron', 'Zinc', 'Protein', 'Vitamin D'],
                'nutrient_explanations': {
                    'Biotin': 'Essential for keratin production - the protein that makes up hair. Deficiency causes hair loss.',
                    'Iron': 'Hair follicles require iron for growth. Iron deficiency is the most common cause of hair loss in women.',
                    'Zinc': 'Crucial for hair tissue growth and repair. Deficiency causes hair loss and slow growth.',
                    'Protein': 'Hair is 95% protein (keratin). Inadequate protein causes weak, brittle, thinning hair.',
                    'Vitamin D': 'Stimulates hair follicles. Low levels associated with alopecia and hair thinning.'
                },
                'foods': ['eggs', 'spinach', 'pumpkin seeds', 'lean meat', 'fatty fish'],
                'sources': ['American Academy of Dermatology', 'NIH Office of Dietary Supplements']
            },
            'brittle_nails': {
                'nutrients': ['Biotin', 'Iron', 'Protein', 'Zinc', 'Vitamin C'],
                'nutrient_explanations': {
                    'Biotin': 'Studies show 25% increase in nail thickness with supplementation. Strengthens nail structure.',
                    'Iron': 'Deficiency causes spoon-shaped, brittle nails. Essential for nail matrix cells.',
                    'Protein': 'Nails are made of keratin protein. Adequate protein essential for strong nails.',
                    'Zinc': 'Required for protein synthesis and cell division in nail matrix.',
                    'Vitamin C': 'Needed for collagen production that supports nail structure. Deficiency causes weak nails.'
                },
                'foods': ['eggs', 'red meat', 'legumes', 'nuts', 'citrus fruits'],
                'sources': ['American Academy of Dermatology', 'NIH Office of Dietary Supplements']
            },

            # Eye Health
            'eye_health': {
                'nutrients': ['Vitamin A', 'Lutein', 'Zeaxanthin', 'Omega-3', 'Vitamin C'],
                'nutrient_explanations': {
                    'Vitamin A': 'Essential for light-detecting cells in retina. Deficiency is leading cause of preventable blindness.',
                    'Lutein': 'Filters harmful blue light and protects macula. Reduces macular degeneration risk by 43%.',
                    'Zeaxanthin': 'Works with lutein in the macula. Antioxidant protection for central vision.',
                    'Omega-3': 'DHA is a major structural component of retina. Reduces dry eye and macular degeneration risk.',
                    'Vitamin C': 'High concentration in eye fluid. Protects against cataracts and age-related damage.'
                },
                'foods': ['carrots', 'spinach', 'eggs', 'salmon', 'citrus fruits'],
                'sources': ['American Academy of Ophthalmology', 'NIH Office of Dietary Supplements']
            },
            'dry_eyes': {
                'nutrients': ['Omega-3', 'Vitamin A', 'Vitamin D', 'Zinc', 'Vitamin E'],
                'nutrient_explanations': {
                    'Omega-3': 'Improves oil layer of tears preventing evaporation. Studies show significant symptom improvement.',
                    'Vitamin A': 'Required for mucin production in tears. Deficiency causes severe dry eye.',
                    'Vitamin D': 'Regulates tear production. Low levels associated with dry eye syndrome.',
                    'Zinc': 'Helps transport vitamin A to eye. Supports tear film stability.',
                    'Vitamin E': 'Antioxidant protection for tear film. Reduces oxidative stress causing dry eye.'
                },
                'foods': ['fatty fish', 'sweet potato', 'egg yolks', 'oysters', 'almonds'],
                'sources': ['American Academy of Ophthalmology', 'NIH Office of Dietary Supplements']
            },

            # Bone Health
            'bone_health': {
                'nutrients': ['Calcium', 'Vitamin D', 'Vitamin K', 'Magnesium', 'Phosphorus'],
                'nutrient_explanations': {
                    'Calcium': '99% of body\'s calcium is in bones. FDA-recognized essential nutrient for bone health.',
                    'Vitamin D': 'Required for calcium absorption. Without adequate D, only 10-15% of calcium is absorbed.',
                    'Vitamin K': 'Activates osteocalcin protein that binds calcium to bones. K2 form most effective.',
                    'Magnesium': '60% stored in bones. Required for vitamin D activation and bone cell function.',
                    'Phosphorus': 'Works with calcium to form bone mineral matrix. Must be balanced with calcium.'
                },
                'foods': ['dairy', 'fortified milk', 'leafy greens', 'nuts', 'fish'],
                'sources': ['NIH Office of Dietary Supplements', 'National Osteoporosis Foundation']
            },
            'osteoporosis': {
                'nutrients': ['Calcium', 'Vitamin D', 'Vitamin K2', 'Magnesium', 'Protein'],
                'nutrient_explanations': {
                    'Calcium': 'Primary building block of bone. Post-menopausal women need 1200mg daily.',
                    'Vitamin D': 'Essential for calcium absorption. Most osteoporosis patients are vitamin D deficient.',
                    'Vitamin K2': 'Directs calcium into bones rather than arteries. Reduces fracture risk.',
                    'Magnesium': 'Deficiency contributes to osteoporosis. Required for bone-building hormone function.',
                    'Protein': 'Makes up 50% of bone volume. Adequate protein reduces fracture risk.'
                },
                'foods': ['dairy products', 'fatty fish', 'natto', 'almonds', 'lean protein'],
                'sources': ['National Osteoporosis Foundation', 'NIH Office of Dietary Supplements']
            },

            # Allergies
            'allergies': {
                'nutrients': ['Quercetin', 'Vitamin C', 'Probiotics', 'Omega-3', 'Bromelain'],
                'nutrient_explanations': {
                    'Quercetin': 'Natural antihistamine that stabilizes mast cells. Prevents histamine release causing symptoms.',
                    'Vitamin C': 'Natural antihistamine and immune modulator. Reduces allergy symptom severity.',
                    'Probiotics': 'Regulate immune response to allergens. Reduce allergic inflammation.',
                    'Omega-3': 'Reduces inflammatory response to allergens. Balances pro-inflammatory omega-6.',
                    'Bromelain': 'Enzyme that reduces nasal swelling and thins mucus. Enhances quercetin absorption.'
                },
                'foods': ['onions', 'citrus', 'yogurt', 'fatty fish', 'pineapple'],
                'sources': ['NIH NCCIH', 'American Academy of Allergy Asthma & Immunology']
            },
            'seasonal_allergies': {
                'nutrients': ['Quercetin', 'Vitamin C', 'Local Honey', 'Probiotics', 'Omega-3'],
                'nutrient_explanations': {
                    'Quercetin': 'Prevents mast cells from releasing histamine. Most effective when taken before allergy season.',
                    'Vitamin C': 'Reduces histamine levels naturally. Supports immune system during allergy season.',
                    'Local Honey': 'May help build tolerance to local pollens. Traditional remedy with some scientific support.',
                    'Probiotics': 'Modulate immune response to reduce allergic reactions. Gut health affects allergies.',
                    'Omega-3': 'Reduces airway inflammation from allergies. May reduce need for antihistamines.'
                },
                'foods': ['apples', 'oranges', 'local honey', 'kefir', 'walnuts'],
                'sources': ['NIH NCCIH', 'American Academy of Allergy Asthma & Immunology']
            },

            # Hormonal Balance
            'hormonal_balance': {
                'nutrients': ['Omega-3', 'Vitamin D', 'B Vitamins', 'Zinc', 'Magnesium'],
                'nutrient_explanations': {
                    'Omega-3': 'Building blocks for hormone production. Reduces inflammation that disrupts hormones.',
                    'Vitamin D': 'Functions as a hormone itself. Regulates many other hormones in the body.',
                    'B Vitamins': 'Essential for hormone synthesis and metabolism. Support adrenal and thyroid function.',
                    'Zinc': 'Required for production of testosterone, estrogen, and thyroid hormones.',
                    'Magnesium': 'Involved in hormone production and regulation. Helps balance cortisol.'
                },
                'foods': ['fatty fish', 'eggs', 'whole grains', 'pumpkin seeds', 'dark chocolate'],
                'sources': ['NIH Office of Dietary Supplements', 'Endocrine Society']
            },
            'pms_symptoms': {
                'nutrients': ['Calcium', 'Magnesium', 'Vitamin B6', 'Vitamin E', 'Omega-3'],
                'nutrient_explanations': {
                    'Calcium': 'Studies show 50% reduction in PMS symptoms with adequate calcium.',
                    'Magnesium': 'Reduces bloating, mood swings, and cramps. Levels drop before menstruation.',
                    'Vitamin B6': 'Reduces PMS mood symptoms. Involved in serotonin production.',
                    'Vitamin E': 'Reduces breast tenderness and cramping. Antioxidant protection.',
                    'Omega-3': 'Reduces inflammation causing cramps. May reduce menstrual pain by 50%.'
                },
                'foods': ['dairy', 'spinach', 'bananas', 'almonds', 'salmon'],
                'sources': ['American College of Obstetricians and Gynecologists', 'NIH Office of Dietary Supplements']
            },
            'menopause_symptoms': {
                'nutrients': ['Phytoestrogens', 'Calcium', 'Vitamin D', 'Omega-3', 'Vitamin E'],
                'nutrient_explanations': {
                    'Phytoestrogens': 'Plant compounds that mildly mimic estrogen. May reduce hot flashes naturally.',
                    'Calcium': 'Bone loss accelerates after menopause. Extra calcium prevents osteoporosis.',
                    'Vitamin D': 'Works with calcium for bone health. Also helps with mood during menopause.',
                    'Omega-3': 'May reduce frequency of hot flashes. Supports heart health post-menopause.',
                    'Vitamin E': 'Studies show reduction in hot flash intensity. Antioxidant protection.'
                },
                'foods': ['soy', 'dairy', 'fatty fish', 'flaxseeds', 'nuts'],
                'sources': ['North American Menopause Society', 'NIH Office of Dietary Supplements']
            },

            # Respiratory
            'respiratory_health': {
                'nutrients': ['Vitamin C', 'Vitamin D', 'Omega-3', 'Magnesium', 'Antioxidants'],
                'nutrient_explanations': {
                    'Vitamin C': 'Protects lung tissue from oxidative damage. Reduces respiratory infection risk.',
                    'Vitamin D': 'Regulates immune response in lungs. Deficiency increases respiratory infection risk.',
                    'Omega-3': 'Reduces airway inflammation. May improve lung function in respiratory conditions.',
                    'Magnesium': 'Relaxes bronchial muscles. Used in emergency asthma treatment.',
                    'Antioxidants': 'Protect lungs from pollution and oxidative stress. Essential for lung health.'
                },
                'foods': ['citrus fruits', 'fatty fish', 'leafy greens', 'berries', 'ginger'],
                'sources': ['American Lung Association', 'NIH Office of Dietary Supplements']
            },
            'asthma_support': {
                'nutrients': ['Vitamin D', 'Magnesium', 'Omega-3', 'Vitamin C', 'Selenium'],
                'nutrient_explanations': {
                    'Vitamin D': 'Low levels triple asthma attack risk. Reduces airway inflammation.',
                    'Magnesium': 'Natural bronchodilator that relaxes airway muscles. IV magnesium used for severe attacks.',
                    'Omega-3': 'Reduces airway inflammation and may decrease asthma medication needs.',
                    'Vitamin C': 'Antioxidant that protects airways. May reduce asthma symptom severity.',
                    'Selenium': 'Antioxidant that reduces airway inflammation. Low levels worsen asthma.'
                },
                'foods': ['fatty fish', 'spinach', 'salmon', 'oranges', 'brazil nuts'],
                'sources': ['American Academy of Allergy Asthma & Immunology', 'NIH Office of Dietary Supplements']
            },

            # Detox and Liver
            'liver_health': {
                'nutrients': ['Milk Thistle', 'Vitamin E', 'Glutathione', 'B Vitamins', 'Selenium'],
                'nutrient_explanations': {
                    'Milk Thistle': 'Contains silymarin which protects liver cells and promotes regeneration.',
                    'Vitamin E': 'Reduces liver inflammation and may slow progression of fatty liver disease.',
                    'Glutathione': 'Master antioxidant produced by liver. Essential for detoxification.',
                    'B Vitamins': 'Required for liver\'s phase 1 and phase 2 detoxification pathways.',
                    'Selenium': 'Cofactor for glutathione production. Protects liver from oxidative damage.'
                },
                'foods': ['coffee', 'grapefruit', 'cruciferous vegetables', 'nuts', 'fatty fish'],
                'sources': ['NIH NCCIH', 'American Liver Foundation']
            },
            'detox': {
                'nutrients': ['Fiber', 'Antioxidants', 'Glutathione', 'Chlorophyll', 'Water'],
                'nutrient_explanations': {
                    'Fiber': 'Binds toxins in gut for elimination. Prevents toxin reabsorption.',
                    'Antioxidants': 'Neutralize free radicals created during detoxification process.',
                    'Glutathione': 'Primary detoxification molecule. Binds to toxins for safe elimination.',
                    'Chlorophyll': 'Binds to heavy metals and environmental toxins. Supports liver function.',
                    'Water': 'Essential for kidney filtration. Flushes toxins from body.'
                },
                'foods': ['leafy greens', 'berries', 'garlic', 'green vegetables', 'lemon water'],
                'sources': ['NIH NCCIH', 'FDA FoodData Central']
            },

            # Headaches
            'headache': {
                'nutrients': ['Magnesium', 'Riboflavin (B2)', 'CoQ10', 'Omega-3', 'Ginger'],
                'nutrient_explanations': {
                    'Magnesium': 'Deficiency is common in headache sufferers. Relaxes blood vessels and muscles.',
                    'Riboflavin (B2)': 'High-dose B2 reduces headache frequency by 50% in studies.',
                    'CoQ10': 'Improves cellular energy in brain. Studies show reduced headache days.',
                    'Omega-3': 'Reduces inflammation that contributes to headaches. May reduce frequency.',
                    'Ginger': 'As effective as sumatriptan for migraine relief in some studies.'
                },
                'foods': ['spinach', 'almonds', 'organ meats', 'fatty fish', 'ginger'],
                'sources': ['American Migraine Foundation', 'NIH Office of Dietary Supplements']
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
                'foods': ['dark leafy greens', 'eggs', 'sardines', 'feverfew tea', 'salmon'],
                'sources': ['American Migraine Foundation', 'NIH NCCIH']
            },

            # Dental Health
            'dental_health': {
                'nutrients': ['Calcium', 'Vitamin D', 'Phosphorus', 'Vitamin C', 'Vitamin A'],
                'nutrient_explanations': {
                    'Calcium': 'Primary mineral in tooth enamel and jaw bone. Essential for strong teeth.',
                    'Vitamin D': 'Required for calcium absorption into teeth. Deficiency weakens tooth structure.',
                    'Phosphorus': 'Works with calcium to mineralize teeth. 85% of phosphorus is in bones and teeth.',
                    'Vitamin C': 'Essential for healthy gums. Deficiency causes bleeding gums and tooth loss.',
                    'Vitamin A': 'Maintains mucous membranes and saliva production. Supports tooth enamel.'
                },
                'foods': ['dairy', 'fatty fish', 'nuts', 'citrus fruits', 'carrots'],
                'sources': ['American Dental Association', 'NIH Office of Dietary Supplements']
            },

            # Pregnancy
            'pregnancy_nutrition': {
                'nutrients': ['Folate', 'Iron', 'Calcium', 'DHA', 'Vitamin D'],
                'nutrient_explanations': {
                    'Folate': 'Prevents neural tube defects. FDA requires fortification of grains. Critical first trimester.',
                    'Iron': 'Blood volume increases 50% during pregnancy. Iron prevents anemia and supports fetal development.',
                    'Calcium': 'Baby draws calcium from mother\'s bones. 1000mg daily prevents bone loss.',
                    'DHA': 'Omega-3 essential for baby\'s brain and eye development. Critical in third trimester.',
                    'Vitamin D': 'Supports fetal bone development and immune system. Many pregnant women are deficient.'
                },
                'foods': ['leafy greens', 'lean meat', 'dairy', 'fatty fish', 'eggs'],
                'sources': ['American College of Obstetricians and Gynecologists', 'NIH Office of Dietary Supplements']
            },

            # Thyroid Health
            'thyroid_health': {
                'nutrients': ['Iodine', 'Selenium', 'Zinc', 'Iron', 'Vitamin D'],
                'nutrient_explanations': {
                    'Iodine': 'Essential for thyroid hormone production (T3 and T4). FDA recommends 150mcg daily. Deficiency causes goiter and hypothyroidism.',
                    'Selenium': 'Required for conversion of T4 to active T3 hormone. Protects thyroid from oxidative damage. Brazil nuts are richest source.',
                    'Zinc': 'Necessary for thyroid hormone synthesis and metabolism. Deficiency impairs thyroid function.',
                    'Iron': 'Required for thyroid peroxidase enzyme that produces thyroid hormones. Iron deficiency reduces thyroid function.',
                    'Vitamin D': 'Low vitamin D associated with autoimmune thyroid conditions. Supports immune regulation.'
                },
                'foods': ['seaweed', 'seafood', 'brazil nuts', 'eggs', 'dairy'],
                'sources': ['NIH Office of Dietary Supplements', 'American Thyroid Association']
            },
            'hypothyroid': {
                'nutrients': ['Iodine', 'Selenium', 'Zinc', 'Vitamin B12', 'Iron'],
                'nutrient_explanations': {
                    'Iodine': 'Building block of thyroid hormones. Without adequate iodine, thyroid cannot produce T3 and T4.',
                    'Selenium': 'Activates thyroid hormones. Studies show selenium improves symptoms in autoimmune thyroiditis.',
                    'Zinc': 'Supports conversion of T4 to T3. Low zinc reduces thyroid hormone levels.',
                    'Vitamin B12': 'Often deficient in hypothyroid patients. Supports energy metabolism impaired by low thyroid.',
                    'Iron': 'Thyroid function depends on iron. Hypothyroidism and iron deficiency often occur together.'
                },
                'foods': ['iodized salt', 'cod', 'shrimp', 'brazil nuts', 'beef liver'],
                'sources': ['NIH Office of Dietary Supplements', 'American Thyroid Association']
            },

            # Nerve Health
            'nerve_health': {
                'nutrients': ['Vitamin B1', 'Vitamin B6', 'Vitamin B12', 'Copper', 'Vitamin E'],
                'nutrient_explanations': {
                    'Vitamin B1': 'Thiamin is essential for nerve signal transmission. Deficiency causes peripheral neuropathy and beriberi.',
                    'Vitamin B6': 'Required for neurotransmitter synthesis including serotonin and dopamine. Deficiency causes numbness and tingling.',
                    'Vitamin B12': 'Maintains myelin sheath protecting nerves. Deficiency causes irreversible nerve damage if untreated.',
                    'Copper': 'Essential for myelin formation and nerve conduction. Deficiency causes myelopathy and neuropathy.',
                    'Vitamin E': 'Antioxidant that protects nerve cell membranes. Deficiency causes neurological problems.'
                },
                'foods': ['pork', 'sunflower seeds', 'fortified cereals', 'shellfish', 'nuts'],
                'sources': ['NIH Office of Dietary Supplements', 'National Institute of Neurological Disorders']
            },
            'neuropathy': {
                'nutrients': ['Vitamin B12', 'Vitamin B1', 'Vitamin B6', 'Alpha-Lipoic Acid', 'Vitamin D'],
                'nutrient_explanations': {
                    'Vitamin B12': 'Most common nutritional cause of neuropathy. Essential for nerve myelin maintenance.',
                    'Vitamin B1': 'Thiamin deficiency causes alcoholic and diabetic neuropathy. Critical for nerve energy metabolism.',
                    'Vitamin B6': 'Supports nerve function but excess can also cause neuropathy. Balance is key.',
                    'Alpha-Lipoic Acid': 'Antioxidant shown to reduce diabetic neuropathy symptoms in clinical trials.',
                    'Vitamin D': 'Low levels associated with peripheral neuropathy. Supports nerve repair.'
                },
                'foods': ['fortified cereals', 'beef', 'pork', 'spinach', 'fatty fish'],
                'sources': ['NIH Office of Dietary Supplements', 'American Diabetes Association']
            },

            # Anemia
            'anemia': {
                'nutrients': ['Iron', 'Vitamin B12', 'Folate', 'Vitamin C', 'Copper'],
                'nutrient_explanations': {
                    'Iron': 'Most common cause of anemia worldwide. Required for hemoglobin production. FDA DV is 18mg.',
                    'Vitamin B12': 'Deficiency causes megaloblastic anemia with large, immature red blood cells.',
                    'Folate': 'Works with B12 for red blood cell formation. Deficiency causes similar anemia to B12.',
                    'Vitamin C': 'Dramatically increases iron absorption from plant sources. Take with iron-rich foods.',
                    'Copper': 'Required for iron transport and red blood cell formation. Deficiency causes anemia even with adequate iron.'
                },
                'foods': ['red meat', 'liver', 'fortified cereals', 'citrus fruits', 'shellfish'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            },

            # Muscle Cramps
            'muscle_cramps': {
                'nutrients': ['Magnesium', 'Potassium', 'Calcium', 'Sodium', 'Vitamin D'],
                'nutrient_explanations': {
                    'Magnesium': 'Regulates muscle contraction and relaxation. Deficiency is a leading cause of cramps.',
                    'Potassium': 'Essential for muscle cell electrical activity. Low potassium causes muscle weakness and cramps.',
                    'Calcium': 'Required for muscle contraction signal. Imbalance causes tetany and cramping.',
                    'Sodium': 'Electrolyte lost in sweat. Exercise-related cramps often due to sodium depletion.',
                    'Vitamin D': 'Supports calcium absorption and muscle function. Deficiency causes muscle weakness.'
                },
                'foods': ['bananas', 'spinach', 'dairy', 'coconut water', 'fortified milk'],
                'sources': ['NIH Office of Dietary Supplements', 'American College of Sports Medicine']
            },

            # Cognitive Health
            'memory': {
                'nutrients': ['Omega-3 DHA', 'Vitamin B12', 'Vitamin E', 'Choline', 'Vitamin D'],
                'nutrient_explanations': {
                    'Omega-3 DHA': 'Makes up 40% of brain fatty acids. Essential for memory and cognitive function.',
                    'Vitamin B12': 'Deficiency causes memory problems and cognitive decline. Critical for brain health.',
                    'Vitamin E': 'Antioxidant that protects brain cells from oxidative damage associated with aging.',
                    'Choline': 'Precursor to acetylcholine neurotransmitter critical for memory. FDA established DV in 2016.',
                    'Vitamin D': 'Receptors throughout brain. Low levels linked to cognitive decline and dementia risk.'
                },
                'foods': ['fatty fish', 'eggs', 'nuts', 'liver', 'fortified milk'],
                'sources': ['NIH Office of Dietary Supplements', 'Alzheimers Association']
            },

            # Skin and Connective Tissue
            'collagen_support': {
                'nutrients': ['Vitamin C', 'Copper', 'Manganese', 'Zinc', 'Protein'],
                'nutrient_explanations': {
                    'Vitamin C': 'Absolutely required for collagen synthesis. Without it, collagen cannot form properly.',
                    'Copper': 'Essential cofactor for lysyl oxidase enzyme that cross-links collagen fibers for strength.',
                    'Manganese': 'Required for procollagen formation. Supports cartilage and bone collagen.',
                    'Zinc': 'Necessary for collagen synthesis enzymes. Supports wound healing and skin integrity.',
                    'Protein': 'Provides amino acids glycine, proline, and hydroxyproline that make up collagen structure.'
                },
                'foods': ['citrus fruits', 'shellfish', 'nuts', 'bone broth', 'lean meat'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            },

            # Energy Metabolism
            'energy_metabolism': {
                'nutrients': ['Vitamin B1', 'Vitamin B2', 'Vitamin B3', 'Vitamin B5', 'Iron'],
                'nutrient_explanations': {
                    'Vitamin B1': 'Thiamin converts carbohydrates to energy. Essential for cellular energy production.',
                    'Vitamin B2': 'Riboflavin is coenzyme in energy metabolism. Required for FAD production.',
                    'Vitamin B3': 'Niacin forms NAD essential for cellular energy. Deficiency causes pellagra.',
                    'Vitamin B5': 'Pantothenic acid forms Coenzyme A, central to energy metabolism. Found in almost all foods.',
                    'Iron': 'Carries oxygen to cells for energy production. Deficiency causes fatigue.'
                },
                'foods': ['whole grains', 'pork', 'fortified cereals', 'mushrooms', 'lean meat'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            },

            # Antioxidant Support
            'antioxidant_support': {
                'nutrients': ['Vitamin C', 'Vitamin E', 'Selenium', 'Manganese', 'Zinc'],
                'nutrient_explanations': {
                    'Vitamin C': 'Water-soluble antioxidant that neutralizes free radicals. Regenerates vitamin E.',
                    'Vitamin E': 'Fat-soluble antioxidant protecting cell membranes. Works with selenium.',
                    'Selenium': 'Component of glutathione peroxidase, a major antioxidant enzyme system.',
                    'Manganese': 'Required for superoxide dismutase (SOD), key mitochondrial antioxidant enzyme.',
                    'Zinc': 'Component of SOD enzyme. Supports overall antioxidant defense system.'
                },
                'foods': ['berries', 'nuts', 'brazil nuts', 'whole grains', 'shellfish'],
                'sources': ['NIH Office of Dietary Supplements', 'FDA FoodData Central']
            }
        }

        # Try to match the condition
        condition_lower = condition.lower().replace(' ', '_').replace('-', '_')

        # Direct match
        if condition_lower in recommendations:
            return recommendations[condition_lower]

        # Partial match
        for key in recommendations:
            if key in condition_lower or condition_lower in key:
                return recommendations[key]

        # Keyword-based matching
        keyword_map = {
            'skin': 'skin_inflammation',
            'tired': 'fatigue',
            'energy': 'energy_metabolism',
            'sleep': 'insomnia',
            'stomach': 'digestive_issues',
            'gut': 'digestive_issues',
            'immune': 'weak_immunity',
            'cold': 'cold_symptoms',
            'heart': 'heart_health',
            'blood': 'high_blood_pressure',
            'sugar': 'blood_sugar',
            'weight': 'weight_loss',
            'hair': 'hair_loss',
            'eye': 'eye_health',
            'bone': 'bone_health',
            'allergy': 'allergies',
            'hormone': 'hormonal_balance',
            'breath': 'respiratory_health',
            'liver': 'liver_health',
            'head': 'headache',
            'teeth': 'dental_health',
            'pregnant': 'pregnancy_nutrition',
            'thyroid': 'thyroid_health',
            'iodine': 'thyroid_health',
            'nerve': 'nerve_health',
            'numbness': 'neuropathy',
            'tingling': 'neuropathy',
            'anemia': 'anemia',
            'iron': 'anemia',
            'cramp': 'muscle_cramps',
            'memory': 'memory',
            'cognitive': 'memory',
            'collagen': 'collagen_support',
            'antioxidant': 'antioxidant_support',
            'metabolism': 'energy_metabolism'
        }

        for keyword, condition_key in keyword_map.items():
            if keyword in condition_lower:
                return recommendations[condition_key]

        # Default to general inflammation
        return recommendations['general_inflammation']
