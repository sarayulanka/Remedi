from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import uuid
from fastapi import HTTPException
from database import get_table, DATA_TYPE_STREAK, DATA_TYPE_BADGE, DATA_TYPE_GOAL

class GamificationService:
    def __init__(self):
        self.table = get_table()

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
                # Create streak record
                streak_data = {
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK,
                    'currentStreak': 0,
                    'longestStreak': 0,
                    'lastCheckIn': None,
                    'totalCheckIns': 0
                }
                self.table.put_item(Item=streak_data)
                return streak_data
            else:
                return response['Item']
        except Exception as e:
            print(f"Error ensuring streak exists: {str(e)}")
            return {
                'currentStreak': 0,
                'longestStreak': 0,
                'lastCheckIn': None,
                'totalCheckIns': 0
            }

    def check_in(self, user_id: str, client_timezone_offset: Optional[int] = None) -> Dict:
        """
        Record a daily check-in and update streak.
        client_timezone_offset: minutes offset from UTC (e.g., -300 for EST)
        """
        try:
            # Get or create streak data
            streak_data = self._ensure_streak_exists(user_id)

            # Use UTC time for consistency
            now = datetime.now(timezone.utc)
            today = now.date()

            last_check_in_str = streak_data.get('lastCheckIn')

            # Calculate new streak
            if last_check_in_str:
                try:
                    # Handle both ISO format with and without timezone
                    if '+' in last_check_in_str or 'Z' in last_check_in_str:
                        last_check_in = datetime.fromisoformat(last_check_in_str.replace('Z', '+00:00'))
                    else:
                        last_check_in = datetime.fromisoformat(last_check_in_str).replace(tzinfo=timezone.utc)

                    last_date = last_check_in.date()
                    days_diff = (today - last_date).days

                    if days_diff == 0:
                        # Already checked in today
                        return {
                            'success': True,
                            'message': 'Already checked in today!',
                            'currentStreak': int(streak_data.get('currentStreak', 0)),
                            'longestStreak': int(streak_data.get('longestStreak', 0)),
                            'totalCheckIns': int(streak_data.get('totalCheckIns', 0)),
                            'newBadges': [],
                            'alreadyCheckedIn': True
                        }
                    elif days_diff == 1:
                        # Consecutive day - increment streak
                        streak_data['currentStreak'] = int(streak_data.get('currentStreak', 0)) + 1
                    elif days_diff > 1:
                        # Streak broken - reset to 1
                        streak_data['currentStreak'] = 1
                    else:
                        # Future date (shouldn't happen) - just set to 1
                        streak_data['currentStreak'] = 1

                except Exception as parse_error:
                    print(f"Error parsing date: {parse_error}")
                    # If date parsing fails, start fresh
                    streak_data['currentStreak'] = 1
            else:
                # First check-in ever
                streak_data['currentStreak'] = 1

            # Ensure currentStreak is an integer
            streak_data['currentStreak'] = int(streak_data.get('currentStreak', 1))
            streak_data['longestStreak'] = int(streak_data.get('longestStreak', 0))

            # Update longest streak if needed
            if streak_data['currentStreak'] > streak_data['longestStreak']:
                streak_data['longestStreak'] = streak_data['currentStreak']

            # Update total check-ins
            streak_data['totalCheckIns'] = int(streak_data.get('totalCheckIns', 0)) + 1

            # Update last check-in time
            streak_data['lastCheckIn'] = now.isoformat()

            # Save updated streak
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK,
                    'currentStreak': streak_data['currentStreak'],
                    'longestStreak': streak_data['longestStreak'],
                    'lastCheckIn': streak_data['lastCheckIn'],
                    'totalCheckIns': streak_data['totalCheckIns']
                }
            )

            # Check for new badges
            new_badges = self._check_streak_badges(user_id, streak_data['currentStreak'])

            return {
                'success': True,
                'message': f'Check-in successful! {streak_data["currentStreak"]}-day streak!',
                'currentStreak': streak_data['currentStreak'],
                'longestStreak': streak_data['longestStreak'],
                'totalCheckIns': streak_data['totalCheckIns'],
                'newBadges': new_badges,
                'alreadyCheckedIn': False
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
            last_check_in_str = streak_data.get('lastCheckIn')

            streak_active = False
            checked_in_today = False
            streak_at_risk = False

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
                    else:
                        # Streak is broken
                        current_streak = 0
                        streak_active = False

                except Exception as parse_error:
                    print(f"Error parsing date in get_streak: {parse_error}")
                    current_streak = 0

            return {
                'currentStreak': current_streak,
                'longestStreak': longest_streak,
                'lastCheckIn': last_check_in_str,
                'totalCheckIns': total_check_ins,
                'streakActive': streak_active,
                'checkedInToday': checked_in_today,
                'streakAtRisk': streak_at_risk
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get streak: {str(e)}"
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
        except:
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
                except:
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

            return {
                'success': True,
                'message': 'Goal completed!' if completed else 'Progress updated!',
                'currentDays': goal['currentDays'],
                'targetDays': int(goal['targetDays']),
                'completed': goal.get('completed', False),
                'newlyCompleted': completed
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
