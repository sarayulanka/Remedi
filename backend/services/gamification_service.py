from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import uuid
import os
import json
from fastapi import HTTPException
from openai import OpenAI
from dotenv import load_dotenv
from database import get_table, DATA_TYPE_STREAK, DATA_TYPE_BADGE, DATA_TYPE_GOAL, DATA_TYPE_FREEZE_LOG, DATA_TYPE_XP, DATA_TYPE_PROFILE

load_dotenv()

# Streak milestone definitions
STREAK_MILESTONES = [3, 7, 14, 30, 50, 100, 365]

MILESTONE_INFO = {
    3: {'name': 'Getting Started', 'xp': 25},
    7: {'name': 'Week Warrior', 'xp': 50},
    14: {'name': 'Two Weeks Strong', 'xp': 100},
    30: {'name': 'Month Master', 'xp': 200},
    50: {'name': '50-Day Legend', 'xp': 300},
    100: {'name': 'Century Club', 'xp': 500},
    365: {'name': 'Year of Wellness', 'xp': 1000}
}

# Grace period in hours past midnight
GRACE_PERIOD_HOURS = 2

# XP System Constants
XP_VALUES = {
    'daily_check_in': 10,
    'complete_goal_day': 25,
    'complete_goal_fully': 100,
    'health_analysis': 15,
    'earn_badge': 50,
    'streak_milestone': 100,  # Base, multiplied by milestone tier
}

# Level progression thresholds
def get_xp_for_level(level: int) -> int:
    """Calculate total XP needed to reach a level"""
    if level <= 1:
        return 0
    if level <= 10:
        return (level - 1) * 100
    if level <= 25:
        return 900 + (level - 10) * 200
    if level <= 50:
        return 3900 + (level - 25) * 350
    return 12650 + (level - 50) * 500

def get_level_from_xp(total_xp: int) -> int:
    """Calculate level from total XP"""
    level = 1
    while get_xp_for_level(level + 1) <= total_xp:
        level += 1
    return level

# Combo multipliers based on actions per day
COMBO_MULTIPLIERS = {
    1: 1.0,
    2: 1.25,
    3: 1.5,
    4: 1.75,
    5: 2.0,  # 5+ actions = 2x multiplier
}

class GamificationService:
    def __init__(self):
        self.table = get_table()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Define available badges
        self.available_badges = {
            'first_day': {
                'name': 'First Step',
                'description': 'Started your nutrition journey',
                'icon': '🌱',
                'requirement': 1
            },
            'week_warrior': {
                'name': 'Week Warrior',
                'description': 'Maintained a 7-day streak',
                'icon': '⭐',
                'requirement': 7
            },
            'ten_day_champion': {
                'name': '10-Day Champion',
                'description': 'Achieved a 10-day streak',
                'icon': '🏆',
                'requirement': 10
            },
            'month_master': {
                'name': 'Month Master',
                'description': 'Maintained a 30-day streak',
                'icon': '👑',
                'requirement': 30
            },
            'fifty_day_legend': {
                'name': '50-Day Legend',
                'description': 'Achieved an incredible 50-day streak',
                'icon': '💎',
                'requirement': 50
            },
            'century_club': {
                'name': 'Century Club',
                'description': 'Reached 100 days of consistent nutrition',
                'icon': '🌟',
                'requirement': 100
            },
            'health_explorer': {
                'name': 'Health Explorer',
                'description': 'Analyzed your first health concern',
                'icon': '🔍',
                'requirement': 'first_analysis'
            },
            'location_scout': {
                'name': 'Location Scout',
                'description': 'Saved your first food location',
                'icon': '📍',
                'requirement': 'first_location'
            },
            'goal_setter': {
                'name': 'Goal Setter',
                'description': 'Created your first nutrition goal',
                'icon': '🎯',
                'requirement': 'first_goal'
            },
            'goal_achiever': {
                'name': 'Goal Achiever',
                'description': 'Completed your first goal',
                'icon': '✅',
                'requirement': 'first_goal_complete'
            }
        }

    def _ensure_streak_exists(self, user_id: str) -> Dict:
        """Ensure streak record exists, create if not"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK
                }
            )

            if 'Item' not in response:
                # Create streak record with enhanced fields
                streak_data = {
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK,
                    'currentStreak': 0,
                    'longestStreak': 0,
                    'lastCheckIn': None,
                    'totalCheckIns': 0,
                    'streakFreezes': 0,
                    'freezesUsed': 0,
                    'lastFreezeEarned': None,
                    'streakMilestones': [],
                    'weeklyCheckIns': 0,
                    'weekStartDate': None
                }
                self.table.put_item(Item=streak_data)
                return streak_data
            else:
                # Ensure existing records have new fields
                item = response['Item']
                if 'streakFreezes' not in item:
                    item['streakFreezes'] = 0
                if 'freezesUsed' not in item:
                    item['freezesUsed'] = 0
                if 'lastFreezeEarned' not in item:
                    item['lastFreezeEarned'] = None
                if 'streakMilestones' not in item:
                    item['streakMilestones'] = []
                if 'weeklyCheckIns' not in item:
                    item['weeklyCheckIns'] = 0
                if 'weekStartDate' not in item:
                    item['weekStartDate'] = None
                return item
        except Exception as e:
            print(f"Error ensuring streak exists: {str(e)}")
            return {
                'currentStreak': 0,
                'longestStreak': 0,
                'lastCheckIn': None,
                'totalCheckIns': 0,
                'streakFreezes': 0,
                'freezesUsed': 0,
                'lastFreezeEarned': None,
                'streakMilestones': [],
                'weeklyCheckIns': 0,
                'weekStartDate': None
            }

    def _get_week_start(self, date) -> str:
        """Get the Monday of the week for a given date"""
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        return monday.isoformat()

    def _is_within_grace_period(self, now: datetime, last_check_in: datetime) -> bool:
        """Check if we're within the grace period (2 hours past midnight)"""
        if now.hour < GRACE_PERIOD_HOURS:
            # We're in the grace period window
            yesterday = (now - timedelta(days=1)).date()
            if last_check_in.date() == yesterday:
                return True
        return False

    def _log_freeze_usage(self, user_id: str, streak_saved: int):
        """Log when a freeze was used"""
        now = datetime.now(timezone.utc)
        self.table.put_item(
            Item={
                'userId': user_id,
                'dataType': f"{DATA_TYPE_FREEZE_LOG}#{now.strftime('%Y-%m-%d')}",
                'usedAt': now.isoformat(),
                'streakSaved': streak_saved
            }
        )

    def check_in(self, user_id: str, goal_id: Optional[str] = None, notes: Optional[str] = None) -> Dict:
        """
        Record a daily check-in and update streak with enhanced logic.
        Includes grace period, streak freezes, and milestone tracking.
        """
        try:
            # Get or create streak data
            streak_data = self._ensure_streak_exists(user_id)

            now = datetime.now(timezone.utc)
            today = now.date()

            last_check_in_str = streak_data.get('lastCheckIn')
            freeze_used = False
            milestone_reached = None
            freeze_earned = False

            # Track weekly check-ins
            current_week_start = self._get_week_start(today)
            stored_week_start = streak_data.get('weekStartDate')

            if stored_week_start != current_week_start:
                # New week, reset weekly check-ins
                streak_data['weeklyCheckIns'] = 0
                streak_data['weekStartDate'] = current_week_start

            # Calculate streak logic
            if last_check_in_str:
                try:
                    if '+' in last_check_in_str or 'Z' in last_check_in_str:
                        last_check_in = datetime.fromisoformat(last_check_in_str.replace('Z', '+00:00'))
                    else:
                        last_check_in = datetime.fromisoformat(last_check_in_str).replace(tzinfo=timezone.utc)

                    last_date = last_check_in.date()
                    days_diff = (today - last_date).days

                    # Check grace period
                    in_grace_period = self._is_within_grace_period(now, last_check_in)

                    if days_diff == 0:
                        # Already checked in today
                        return {
                            'success': True,
                            'message': 'Already checked in today!',
                            'currentStreak': int(streak_data.get('currentStreak', 0)),
                            'longestStreak': int(streak_data.get('longestStreak', 0)),
                            'totalCheckIns': int(streak_data.get('totalCheckIns', 0)),
                            'streakFreezes': int(streak_data.get('streakFreezes', 0)),
                            'newBadges': [],
                            'alreadyCheckedIn': True,
                            'freezeUsed': False,
                            'milestoneReached': None,
                            'freezeEarned': False
                        }
                    elif days_diff == 1 or (days_diff == 1 and in_grace_period):
                        # Consecutive day - increment streak
                        streak_data['currentStreak'] = int(streak_data.get('currentStreak', 0)) + 1
                    elif days_diff == 2 and in_grace_period:
                        # Within grace period, treat as consecutive
                        streak_data['currentStreak'] = int(streak_data.get('currentStreak', 0)) + 1
                    elif days_diff > 1:
                        # Streak would be broken - try to use freeze
                        current_freezes = int(streak_data.get('streakFreezes', 0))
                        current_streak = int(streak_data.get('currentStreak', 0))

                        if current_freezes > 0 and current_streak > 0:
                            # Auto-use freeze to save streak
                            streak_data['streakFreezes'] = current_freezes - 1
                            streak_data['freezesUsed'] = int(streak_data.get('freezesUsed', 0)) + 1
                            streak_data['currentStreak'] = current_streak + 1
                            freeze_used = True
                            self._log_freeze_usage(user_id, current_streak)
                        else:
                            # Streak broken - reset to 1
                            streak_data['currentStreak'] = 1
                    else:
                        streak_data['currentStreak'] = 1

                except Exception as parse_error:
                    print(f"Error parsing date: {parse_error}")
                    streak_data['currentStreak'] = 1
            else:
                # First check-in ever
                streak_data['currentStreak'] = 1

            # Ensure values are integers
            streak_data['currentStreak'] = int(streak_data.get('currentStreak', 1))
            streak_data['longestStreak'] = int(streak_data.get('longestStreak', 0))

            # Update longest streak if needed
            if streak_data['currentStreak'] > streak_data['longestStreak']:
                streak_data['longestStreak'] = streak_data['currentStreak']

            # Update total and weekly check-ins
            streak_data['totalCheckIns'] = int(streak_data.get('totalCheckIns', 0)) + 1
            streak_data['weeklyCheckIns'] = int(streak_data.get('weeklyCheckIns', 0)) + 1

            # Update last check-in time
            streak_data['lastCheckIn'] = now.isoformat()

            # Check for milestone achievement
            current_milestones = streak_data.get('streakMilestones', [])
            if not isinstance(current_milestones, list):
                current_milestones = []

            for milestone in STREAK_MILESTONES:
                if streak_data['currentStreak'] >= milestone and milestone not in current_milestones:
                    current_milestones.append(milestone)
                    milestone_reached = {
                        'days': milestone,
                        'name': MILESTONE_INFO[milestone]['name'],
                        'xp': MILESTONE_INFO[milestone]['xp']
                    }
            streak_data['streakMilestones'] = current_milestones

            # Award streak freeze every 7 consecutive days (once per week)
            last_freeze_earned = streak_data.get('lastFreezeEarned')
            can_earn_freeze = True

            if last_freeze_earned:
                try:
                    last_freeze_date = datetime.fromisoformat(last_freeze_earned).date()
                    days_since_freeze = (today - last_freeze_date).days
                    if days_since_freeze < 7:
                        can_earn_freeze = False
                except (ValueError, TypeError):
                    pass

            if streak_data['currentStreak'] > 0 and streak_data['currentStreak'] % 7 == 0 and can_earn_freeze:
                streak_data['streakFreezes'] = int(streak_data.get('streakFreezes', 0)) + 1
                streak_data['lastFreezeEarned'] = today.isoformat()
                freeze_earned = True

            # Save updated streak
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK,
                    'currentStreak': streak_data['currentStreak'],
                    'longestStreak': streak_data['longestStreak'],
                    'lastCheckIn': streak_data['lastCheckIn'],
                    'totalCheckIns': streak_data['totalCheckIns'],
                    'streakFreezes': streak_data.get('streakFreezes', 0),
                    'freezesUsed': streak_data.get('freezesUsed', 0),
                    'lastFreezeEarned': streak_data.get('lastFreezeEarned'),
                    'streakMilestones': streak_data.get('streakMilestones', []),
                    'weeklyCheckIns': streak_data.get('weeklyCheckIns', 0),
                    'weekStartDate': streak_data.get('weekStartDate')
                }
            )

            # Check for new badges
            new_badges = self._check_streak_badges(user_id, streak_data['currentStreak'])

            # Award XP for check-in
            xp_result = self.award_xp(user_id, 'daily_check_in')

            # Award bonus XP for milestone
            if milestone_reached:
                milestone_xp = milestone_reached.get('xp', 100)
                self.award_xp(user_id, 'streak_milestone', milestone_xp)
                xp_result['xpAwarded'] = xp_result.get('xpAwarded', 0) + milestone_xp

            # Build response message
            message = f'Check-in successful! {streak_data["currentStreak"]}-day streak!'
            if freeze_used:
                message = f'Streak saved with freeze! {streak_data["currentStreak"]}-day streak!'
            if freeze_earned:
                message += ' You earned a streak freeze!'

            return {
                'success': True,
                'message': message,
                'currentStreak': streak_data['currentStreak'],
                'longestStreak': streak_data['longestStreak'],
                'totalCheckIns': streak_data['totalCheckIns'],
                'streakFreezes': streak_data.get('streakFreezes', 0),
                'weeklyCheckIns': streak_data.get('weeklyCheckIns', 0),
                'newBadges': new_badges,
                'alreadyCheckedIn': False,
                'freezeUsed': freeze_used,
                'milestoneReached': milestone_reached,
                'freezeEarned': freeze_earned,
                'xp': xp_result
            }

        except Exception as e:
            print(f"Check-in error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check in: {str(e)}"
            )

    def get_streak(self, user_id: str) -> Dict:
        """Get user's current streak information with status"""
        try:
            streak_data = self._ensure_streak_exists(user_id)

            # Check if streak is still active (checked in today or yesterday)
            current_streak = int(streak_data.get('currentStreak', 0))
            longest_streak = int(streak_data.get('longestStreak', 0))
            total_check_ins = int(streak_data.get('totalCheckIns', 0))
            streak_freezes = int(streak_data.get('streakFreezes', 0))
            weekly_check_ins = int(streak_data.get('weeklyCheckIns', 0))
            last_check_in_str = streak_data.get('lastCheckIn')
            streak_milestones = streak_data.get('streakMilestones', [])

            streak_active = False
            checked_in_today = False
            streak_at_risk = False
            has_freeze_protection = streak_freezes > 0

            if last_check_in_str:
                try:
                    if '+' in last_check_in_str or 'Z' in last_check_in_str:
                        last_check_in = datetime.fromisoformat(last_check_in_str.replace('Z', '+00:00'))
                    else:
                        last_check_in = datetime.fromisoformat(last_check_in_str).replace(tzinfo=timezone.utc)

                    now = datetime.now(timezone.utc)
                    days_diff = (now.date() - last_check_in.date()).days

                    if days_diff == 0:
                        streak_active = True
                        checked_in_today = True
                    elif days_diff == 1:
                        streak_active = True
                        streak_at_risk = True  # Haven't checked in today yet
                    elif days_diff > 1 and has_freeze_protection:
                        # Streak would be at risk but freeze available
                        streak_active = True
                        streak_at_risk = True
                    else:
                        # Streak is broken
                        current_streak = 0
                        streak_active = False

                except Exception as parse_error:
                    print(f"Error parsing date in get_streak: {parse_error}")
                    current_streak = 0

            # Calculate next milestone
            next_milestone = None
            days_to_next_milestone = None
            for milestone in STREAK_MILESTONES:
                if current_streak < milestone:
                    next_milestone = {
                        'days': milestone,
                        'name': MILESTONE_INFO[milestone]['name'],
                        'xp': MILESTONE_INFO[milestone]['xp']
                    }
                    days_to_next_milestone = milestone - current_streak
                    break

            # Calculate progress to next freeze (awarded every 7 days)
            days_until_freeze = 7 - (current_streak % 7) if current_streak % 7 != 0 else 7

            return {
                'currentStreak': current_streak,
                'longestStreak': longest_streak,
                'lastCheckIn': last_check_in_str,
                'totalCheckIns': total_check_ins,
                'streakActive': streak_active,
                'checkedInToday': checked_in_today,
                'streakAtRisk': streak_at_risk,
                'streakFreezes': streak_freezes,
                'hasFreezeProtection': has_freeze_protection,
                'weeklyCheckIns': weekly_check_ins,
                'achievedMilestones': streak_milestones,
                'nextMilestone': next_milestone,
                'daysToNextMilestone': days_to_next_milestone,
                'daysUntilFreeze': days_until_freeze
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get streak: {str(e)}"
            )

    def get_milestones(self, user_id: str) -> Dict:
        """Get detailed milestone progress for user"""
        try:
            streak_data = self._ensure_streak_exists(user_id)
            current_streak = int(streak_data.get('currentStreak', 0))
            achieved_milestones = streak_data.get('streakMilestones', [])

            milestones = []
            for milestone_days in STREAK_MILESTONES:
                milestone_info = MILESTONE_INFO[milestone_days]
                achieved = milestone_days in achieved_milestones
                progress = min(100, round((current_streak / milestone_days) * 100, 1))

                milestones.append({
                    'days': milestone_days,
                    'name': milestone_info['name'],
                    'xp': milestone_info['xp'],
                    'achieved': achieved,
                    'progress': progress if not achieved else 100,
                    'daysRemaining': max(0, milestone_days - current_streak)
                })

            return {
                'currentStreak': current_streak,
                'milestones': milestones
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get milestones: {str(e)}"
            )

    def use_streak_freeze(self, user_id: str) -> Dict:
        """Manually use a streak freeze (for testing or future features)"""
        try:
            streak_data = self._ensure_streak_exists(user_id)
            current_freezes = int(streak_data.get('streakFreezes', 0))

            if current_freezes <= 0:
                raise HTTPException(status_code=400, detail="No streak freezes available")

            # This is primarily for the auto-use feature, but exposed for testing
            return {
                'success': True,
                'message': 'Freeze is available and will be auto-used if needed',
                'streakFreezes': current_freezes
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to use freeze: {str(e)}"
            )

    def _check_streak_badges(self, user_id: str, current_streak: int) -> List[Dict]:
        """Check if user earned any new streak badges"""
        new_badges = []

        # Check streak milestones
        for badge_id, badge_info in self.available_badges.items():
            if isinstance(badge_info['requirement'], int) and current_streak >= badge_info['requirement']:
                # Check if badge already earned
                if not self._has_badge(user_id, badge_id):
                    self._award_badge(user_id, badge_id, badge_info)
                    new_badges.append({
                        'badgeId': badge_id,
                        **badge_info
                    })

        return new_badges

    def award_activity_badge(self, user_id: str, activity: str) -> Dict:
        """Award a badge for completing an activity"""
        badge_map = {
            'first_analysis': 'health_explorer',
            'first_location': 'location_scout',
            'first_goal': 'goal_setter',
            'first_goal_complete': 'goal_achiever'
        }

        badge_id = badge_map.get(activity)
        if not badge_id:
            return {'message': 'Invalid activity'}

        if self._has_badge(user_id, badge_id):
            return {'message': 'Badge already earned'}

        badge_info = self.available_badges[badge_id]
        self._award_badge(user_id, badge_id, badge_info)

        return {
            'message': 'Badge earned!',
            'badge': {
                'badgeId': badge_id,
                **badge_info
            }
        }

    def _has_badge(self, user_id: str, badge_id: str) -> bool:
        """Check if user already has a badge"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_BADGE}#{badge_id}"
                }
            )
            return 'Item' in response
        except Exception:
            return False

    def _award_badge(self, user_id: str, badge_id: str, badge_info: Dict):
        """Award a badge to a user"""
        try:
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_BADGE}#{badge_id}",
                    'badgeId': badge_id,
                    'name': badge_info['name'],
                    'description': badge_info['description'],
                    'icon': badge_info['icon'],
                    'earnedAt': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            print(f"Error awarding badge: {str(e)}")

    def get_badges(self, user_id: str) -> List[Dict]:
        """Get all badges earned by user"""
        try:
            response = self.table.query(
                KeyConditionExpression='userId = :userId AND begins_with(dataType, :dataType)',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':dataType': DATA_TYPE_BADGE
                }
            )

            return response.get('Items', [])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get badges: {str(e)}"
            )

    def create_goal(self, user_id: str, title: str, description: str, target_days: int) -> Dict:
        """Create a new nutrition goal"""
        goal_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_GOAL}#{goal_id}",
                    'goalId': goal_id,
                    'title': title,
                    'description': description,
                    'targetDays': target_days,
                    'currentDays': 0,
                    'completed': False,
                    'createdAt': timestamp,
                    'completedAt': '',
                    'lastProgressUpdate': None
                }
            )

            # Award first goal badge
            self.award_activity_badge(user_id, 'first_goal')

            return {
                'goalId': goal_id,
                'message': 'Goal created successfully'
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create goal: {str(e)}"
            )

    def update_goal_progress(self, user_id: str, goal_id: str) -> Dict:
        """Update progress on a goal - can only update once per day"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_GOAL}#{goal_id}"
                }
            )

            if 'Item' not in response:
                raise HTTPException(status_code=404, detail="Goal not found")

            goal = response['Item']

            if goal.get('completed'):
                return {
                    'success': True,
                    'message': 'Goal already completed!',
                    'currentDays': int(goal['currentDays']),
                    'targetDays': int(goal['targetDays']),
                    'completed': True
                }

            # Check if already updated today
            last_update = goal.get('lastProgressUpdate')
            now = datetime.now(timezone.utc)

            if last_update:
                try:
                    if '+' in last_update or 'Z' in last_update:
                        last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    else:
                        last_update_dt = datetime.fromisoformat(last_update).replace(tzinfo=timezone.utc)

                    if last_update_dt.date() == now.date():
                        return {
                            'success': True,
                            'message': 'Already logged progress today!',
                            'currentDays': int(goal['currentDays']),
                            'targetDays': int(goal['targetDays']),
                            'completed': goal.get('completed', False),
                            'alreadyUpdated': True
                        }
                except (ValueError, TypeError):
                    pass

            # Update progress
            goal['currentDays'] = int(goal.get('currentDays', 0)) + 1
            goal['lastProgressUpdate'] = now.isoformat()

            # Check if goal is completed
            completed = False
            if goal['currentDays'] >= int(goal['targetDays']):
                goal['completed'] = True
                goal['completedAt'] = now.isoformat()
                completed = True

                # Award completion badge
                self.award_activity_badge(user_id, 'first_goal_complete')

            # Save updated goal
            self.table.put_item(Item={
                'userId': user_id,
                'dataType': f"{DATA_TYPE_GOAL}#{goal_id}",
                **{k: v for k, v in goal.items() if k not in ['userId', 'dataType']}
            })

            # Award XP for goal progress
            xp_result = self.award_xp(user_id, 'complete_goal_day')

            # Award bonus XP for completing the goal entirely
            if completed:
                bonus_xp = self.award_xp(user_id, 'complete_goal_fully')
                xp_result['xpAwarded'] = xp_result.get('xpAwarded', 0) + bonus_xp.get('xpAwarded', 0)
                xp_result['levelUp'] = xp_result.get('levelUp', False) or bonus_xp.get('levelUp', False)
                if bonus_xp.get('newLevel'):
                    xp_result['newLevel'] = bonus_xp['newLevel']

            return {
                'success': True,
                'message': 'Goal completed!' if completed else 'Progress updated!',
                'currentDays': goal['currentDays'],
                'targetDays': int(goal['targetDays']),
                'completed': goal.get('completed', False),
                'newlyCompleted': completed,
                'xp': xp_result
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update goal: {str(e)}"
            )

    def delete_goal(self, user_id: str, goal_id: str) -> Dict:
        """Delete a goal"""
        try:
            self.table.delete_item(
                Key={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_GOAL}#{goal_id}"
                }
            )
            return {'message': 'Goal deleted successfully'}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete goal: {str(e)}"
            )

    def get_goals(self, user_id: str) -> List[Dict]:
        """Get all goals for a user"""
        try:
            response = self.table.query(
                KeyConditionExpression='userId = :userId AND begins_with(dataType, :dataType)',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':dataType': DATA_TYPE_GOAL
                }
            )

            # Convert numeric fields and add calculated fields
            goals = []
            for goal in response.get('Items', []):
                processed_goal = {
                    **goal,
                    'currentDays': int(goal.get('currentDays', 0)),
                    'targetDays': int(goal.get('targetDays', 0)),
                    'progress': round((int(goal.get('currentDays', 0)) / max(int(goal.get('targetDays', 1)), 1)) * 100, 1)
                }
                goals.append(processed_goal)

            return goals
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get goals: {str(e)}"
            )

    def get_all_available_badges(self) -> List[Dict]:
        """Get list of all available badges"""
        return [
            {
                'badgeId': badge_id,
                **badge_info
            }
            for badge_id, badge_info in self.available_badges.items()
        ]

    # ==================== XP SYSTEM METHODS ====================

    def _ensure_xp_exists(self, user_id: str) -> Dict:
        """Ensure XP record exists, create if not"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': DATA_TYPE_XP
                }
            )

            if 'Item' not in response:
                # Create XP record
                now = datetime.now(timezone.utc)
                xp_data = {
                    'userId': user_id,
                    'dataType': DATA_TYPE_XP,
                    'totalXP': 0,
                    'currentLevel': 1,
                    'xpToNextLevel': 100,
                    'xpProgress': 0,
                    'weeklyXP': 0,
                    'todayXP': 0,
                    'lastXPAction': None,
                    'lastXPDate': None,
                    'comboMultiplier': 1.0,
                    'comboActions': 0,
                    'xpHistory': []
                }
                self.table.put_item(Item=xp_data)
                return xp_data
            else:
                item = response['Item']
                # Ensure all fields exist
                defaults = {
                    'totalXP': 0,
                    'currentLevel': 1,
                    'xpToNextLevel': 100,
                    'xpProgress': 0,
                    'weeklyXP': 0,
                    'todayXP': 0,
                    'lastXPAction': None,
                    'lastXPDate': None,
                    'comboMultiplier': 1.0,
                    'comboActions': 0,
                    'xpHistory': []
                }
                for key, default_val in defaults.items():
                    if key not in item:
                        item[key] = default_val
                return item
        except Exception as e:
            print(f"Error ensuring XP exists: {str(e)}")
            return {
                'totalXP': 0,
                'currentLevel': 1,
                'xpToNextLevel': 100,
                'xpProgress': 0,
                'weeklyXP': 0,
                'todayXP': 0,
                'comboMultiplier': 1.0,
                'comboActions': 0,
                'xpHistory': []
            }

    def award_xp(self, user_id: str, action: str, base_amount: Optional[int] = None) -> Dict:
        """
        Award XP to user for an action.
        Applies combo multiplier and tracks level progression.
        """
        try:
            xp_data = self._ensure_xp_exists(user_id)
            now = datetime.now(timezone.utc)
            today = now.date().isoformat()

            # Get base XP amount
            if base_amount is None:
                base_amount = XP_VALUES.get(action, 10)

            # Check if it's a new day - reset daily counters
            last_xp_date = xp_data.get('lastXPDate')
            if last_xp_date != today:
                xp_data['todayXP'] = 0
                xp_data['comboActions'] = 0
                xp_data['comboMultiplier'] = 1.0

            # Update combo
            xp_data['comboActions'] = int(xp_data.get('comboActions', 0)) + 1
            combo_actions = xp_data['comboActions']
            multiplier = COMBO_MULTIPLIERS.get(min(combo_actions, 5), 2.0)
            xp_data['comboMultiplier'] = multiplier

            # Calculate final XP with multiplier
            final_xp = int(base_amount * multiplier)

            # Update XP totals
            old_total = int(xp_data.get('totalXP', 0))
            new_total = old_total + final_xp
            xp_data['totalXP'] = new_total
            xp_data['todayXP'] = int(xp_data.get('todayXP', 0)) + final_xp
            xp_data['weeklyXP'] = int(xp_data.get('weeklyXP', 0)) + final_xp
            xp_data['lastXPAction'] = now.isoformat()
            xp_data['lastXPDate'] = today

            # Calculate level progression
            old_level = get_level_from_xp(old_total)
            new_level = get_level_from_xp(new_total)
            level_up = new_level > old_level

            xp_data['currentLevel'] = new_level

            # Calculate XP progress to next level
            xp_for_current_level = get_xp_for_level(new_level)
            xp_for_next_level = get_xp_for_level(new_level + 1)
            xp_data['xpProgress'] = new_total - xp_for_current_level
            xp_data['xpToNextLevel'] = xp_for_next_level - xp_for_current_level

            # Update XP history (keep last 7 days)
            xp_history = xp_data.get('xpHistory', [])
            if not isinstance(xp_history, list):
                xp_history = []

            # Find or create today's entry
            today_entry = next((h for h in xp_history if h.get('date') == today), None)
            if today_entry:
                today_entry['xp'] = int(today_entry.get('xp', 0)) + final_xp
            else:
                xp_history.append({'date': today, 'xp': final_xp})

            # Keep only last 7 days
            xp_history = sorted(xp_history, key=lambda x: x['date'], reverse=True)[:7]
            xp_data['xpHistory'] = xp_history

            # Save updated XP data
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': DATA_TYPE_XP,
                    'totalXP': xp_data['totalXP'],
                    'currentLevel': xp_data['currentLevel'],
                    'xpToNextLevel': xp_data['xpToNextLevel'],
                    'xpProgress': xp_data['xpProgress'],
                    'weeklyXP': xp_data['weeklyXP'],
                    'todayXP': xp_data['todayXP'],
                    'lastXPAction': xp_data['lastXPAction'],
                    'lastXPDate': xp_data['lastXPDate'],
                    'comboMultiplier': xp_data['comboMultiplier'],
                    'comboActions': xp_data['comboActions'],
                    'xpHistory': xp_data['xpHistory']
                }
            )

            return {
                'success': True,
                'xpAwarded': final_xp,
                'baseXP': base_amount,
                'multiplier': multiplier,
                'totalXP': xp_data['totalXP'],
                'currentLevel': xp_data['currentLevel'],
                'xpProgress': xp_data['xpProgress'],
                'xpToNextLevel': xp_data['xpToNextLevel'],
                'levelUp': level_up,
                'newLevel': new_level if level_up else None,
                'comboActions': xp_data['comboActions'],
                'comboMultiplier': multiplier
            }

        except Exception as e:
            print(f"Error awarding XP: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to award XP: {str(e)}"
            )

    def get_xp(self, user_id: str) -> Dict:
        """Get user's current XP and level status"""
        try:
            xp_data = self._ensure_xp_exists(user_id)
            now = datetime.now(timezone.utc)
            today = now.date().isoformat()

            # Check if we need to reset daily counters
            last_xp_date = xp_data.get('lastXPDate')
            if last_xp_date != today:
                xp_data['todayXP'] = 0
                xp_data['comboActions'] = 0
                xp_data['comboMultiplier'] = 1.0

            # Ensure numeric values
            total_xp = int(xp_data.get('totalXP', 0))
            current_level = get_level_from_xp(total_xp)
            xp_for_current = get_xp_for_level(current_level)
            xp_for_next = get_xp_for_level(current_level + 1)

            return {
                'totalXP': total_xp,
                'currentLevel': current_level,
                'xpProgress': total_xp - xp_for_current,
                'xpToNextLevel': xp_for_next - xp_for_current,
                'progressPercent': round(((total_xp - xp_for_current) / max(xp_for_next - xp_for_current, 1)) * 100, 1),
                'weeklyXP': int(xp_data.get('weeklyXP', 0)),
                'todayXP': int(xp_data.get('todayXP', 0)),
                'comboMultiplier': float(xp_data.get('comboMultiplier', 1.0)),
                'comboActions': int(xp_data.get('comboActions', 0)),
                'nextComboMultiplier': COMBO_MULTIPLIERS.get(min(int(xp_data.get('comboActions', 0)) + 1, 5), 2.0)
            }

        except Exception as e:
            print(f"Error getting XP: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get XP: {str(e)}"
            )

    def get_xp_history(self, user_id: str) -> Dict:
        """Get user's XP history for charts"""
        try:
            xp_data = self._ensure_xp_exists(user_id)

            xp_history = xp_data.get('xpHistory', [])
            if not isinstance(xp_history, list):
                xp_history = []

            # Sort by date
            xp_history = sorted(xp_history, key=lambda x: x.get('date', ''), reverse=True)

            # Calculate 7-day average
            total_7_days = sum(h.get('xp', 0) for h in xp_history[:7])
            avg_daily = round(total_7_days / max(len(xp_history[:7]), 1), 1)

            return {
                'history': xp_history,
                'totalLast7Days': total_7_days,
                'averageDaily': avg_daily,
                'totalXP': int(xp_data.get('totalXP', 0)),
                'currentLevel': int(xp_data.get('currentLevel', 1))
            }

        except Exception as e:
            print(f"Error getting XP history: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get XP history: {str(e)}"
            )

    # ==================== AI GOAL GENERATION ====================

    def _get_user_profile(self, user_id: str) -> Dict:
        """Get user profile for personalized goal generation"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': DATA_TYPE_PROFILE
                }
            )
            return response.get('Item', {})
        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return {}

    def check_and_generate_goals(self, user_id: str) -> Dict:
        """Check if all goals are completed and generate new ones if needed"""
        try:
            # Get all goals
            goals = self.get_goals(user_id)

            # Check if there are any active (non-completed) goals
            active_goals = [g for g in goals if not g.get('completed', False)]
            completed_goals = [g for g in goals if g.get('completed', False)]

            # If there are still active goals, no need to generate
            if active_goals:
                return {
                    'generated': False,
                    'message': 'You still have active goals to complete!',
                    'activeGoals': len(active_goals),
                    'completedGoals': len(completed_goals)
                }

            # All goals completed (or no goals exist) - generate new ones
            new_goals = self._generate_ai_goals(user_id, completed_goals)

            # Create the new goals
            created_goals = []
            for goal in new_goals:
                result = self.create_goal(
                    user_id=user_id,
                    title=goal['title'],
                    description=goal['description'],
                    target_days=goal['targetDays']
                )
                created_goals.append({
                    'goalId': result['goalId'],
                    'title': goal['title'],
                    'description': goal['description'],
                    'targetDays': goal['targetDays']
                })

            return {
                'generated': True,
                'message': f'Generated {len(created_goals)} new personalized goals!',
                'newGoals': created_goals,
                'completedGoals': len(completed_goals)
            }

        except Exception as e:
            print(f"Error in check_and_generate_goals: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check/generate goals: {str(e)}"
            )

    def _generate_ai_goals(self, user_id: str, completed_goals: List[Dict]) -> List[Dict]:
        """Use AI to generate personalized nutrition goals"""
        try:
            # Get user profile for personalization
            profile = self._get_user_profile(user_id)

            # Build context from completed goals
            completed_titles = [g.get('title', '') for g in completed_goals[-10:]]  # Last 10 completed

            # Get user's health info
            health_conditions = profile.get('healthConditions', [])
            nutrition_goals = profile.get('nutritionGoals', [])
            allergies = profile.get('allergies', [])
            diet_type = profile.get('dietType', '')

            prompt = f"""Generate 3 personalized nutrition goals for a user with the following profile:

Health Conditions: {', '.join(health_conditions) if health_conditions else 'None specified'}
Nutrition Goals: {', '.join(nutrition_goals) if nutrition_goals else 'General wellness'}
Allergies/Restrictions: {', '.join(allergies) if allergies else 'None'}
Diet Type: {diet_type if diet_type else 'No specific diet'}

Previously completed goals: {', '.join(completed_titles) if completed_titles else 'None yet - this is their first set of goals'}

Generate 3 NEW, different goals that:
1. Are specific and actionable (not vague like "eat healthier")
2. Have clear daily actions the user can track
3. Range from easy (3-5 days) to moderate (7-14 days) to challenging (21-30 days)
4. Are appropriate for their health conditions and dietary restrictions
5. Build upon or complement their previous goals (if any)
6. Focus on nutrition, hydration, or healthy eating habits

Return ONLY a JSON array with exactly 3 goals in this format:
[
  {{
    "title": "Short goal title (max 40 chars)",
    "description": "Clear description of what to do daily",
    "targetDays": 5
  }},
  {{
    "title": "Medium difficulty goal",
    "description": "Description",
    "targetDays": 10
  }},
  {{
    "title": "Challenging goal",
    "description": "Description",
    "targetDays": 21
  }}
]

Example goals:
- "Drink 8 glasses of water daily" (7 days)
- "Eat leafy greens with every lunch" (14 days)
- "Replace sugary snacks with fruits" (21 days)
- "Take a probiotic food daily" (10 days)
- "Eat protein with breakfast" (7 days)

Return ONLY the JSON array, no other text."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a nutrition coach that creates personalized, achievable goals. Always return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Parse the response
            content = response.choices[0].message.content.strip()

            # Clean up the response if it has markdown code blocks
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()

            goals = json.loads(content)

            # Validate and sanitize
            validated_goals = []
            for goal in goals[:3]:  # Max 3 goals
                validated_goals.append({
                    'title': str(goal.get('title', 'Nutrition Goal'))[:50],
                    'description': str(goal.get('description', 'Complete this daily nutrition goal'))[:200],
                    'targetDays': min(max(int(goal.get('targetDays', 7)), 3), 30)  # Between 3 and 30 days
                })

            return validated_goals

        except json.JSONDecodeError as e:
            print(f"JSON parse error in AI goal generation: {str(e)}")
            # Return default goals if AI fails
            return self._get_default_goals()
        except Exception as e:
            print(f"Error generating AI goals: {str(e)}")
            return self._get_default_goals()

    def _get_default_goals(self) -> List[Dict]:
        """Return default goals if AI generation fails"""
        return [
            {
                'title': 'Stay Hydrated',
                'description': 'Drink at least 8 glasses of water throughout the day',
                'targetDays': 7
            },
            {
                'title': 'Eat More Vegetables',
                'description': 'Include at least 2 servings of vegetables in your meals',
                'targetDays': 14
            },
            {
                'title': 'Mindful Eating',
                'description': 'Eat one meal per day without screens, focusing on your food',
                'targetDays': 21
            }
        ]
