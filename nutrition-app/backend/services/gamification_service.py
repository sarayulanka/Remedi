from datetime import datetime, timedelta
from typing import List, Dict
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
    
    def check_in(self, user_id: str) -> Dict:
        """Record a daily check-in and update streak"""
        try:
            # Get current streak data
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK
                }
            )
            
            if 'Item' not in response:
                # Initialize streak
                streak_data = {
                    'currentStreak': 0,
                    'longestStreak': 0,
                    'lastCheckIn': None
                }
            else:
                streak_data = response['Item']
            
            now = datetime.utcnow()
            last_check_in = streak_data.get('lastCheckIn')
            
            # Calculate new streak
            if last_check_in:
                last_date = datetime.fromisoformat(last_check_in)
                days_diff = (now.date() - last_date.date()).days
                
                if days_diff == 0:
                    # Already checked in today
                    return {
                        'message': 'Already checked in today',
                        'currentStreak': streak_data['currentStreak'],
                        'longestStreak': streak_data['longestStreak'],
                        'newBadges': []
                    }
                elif days_diff == 1:
                    # Consecutive day
                    streak_data['currentStreak'] += 1
                else:
                    # Streak broken
                    streak_data['currentStreak'] = 1
            else:
                # First check-in
                streak_data['currentStreak'] = 1
            
            # Update longest streak
            if streak_data['currentStreak'] > streak_data.get('longestStreak', 0):
                streak_data['longestStreak'] = streak_data['currentStreak']
            
            streak_data['lastCheckIn'] = now.isoformat()
            
            # Save updated streak
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK,
                    **streak_data
                }
            )
            
            # Check for new badges
            new_badges = self._check_streak_badges(user_id, streak_data['currentStreak'])
            
            return {
                'message': 'Check-in successful',
                'currentStreak': streak_data['currentStreak'],
                'longestStreak': streak_data['longestStreak'],
                'newBadges': new_badges
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check in: {str(e)}"
            )
    
    def get_streak(self, user_id: str) -> Dict:
        """Get user's current streak information"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': DATA_TYPE_STREAK
                }
            )
            
            if 'Item' not in response:
                return {
                    'currentStreak': 0,
                    'longestStreak': 0,
                    'lastCheckIn': None
                }
            
            return response['Item']
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
                    'earnedAt': datetime.utcnow().isoformat()
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
        timestamp = datetime.utcnow().isoformat()
        
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
                    'completedAt': ''
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
        """Update progress on a goal"""
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
            
            if goal['completed']:
                return {'message': 'Goal already completed'}
            
            goal['currentDays'] += 1
            
            # Check if goal is completed
            if goal['currentDays'] >= goal['targetDays']:
                goal['completed'] = True
                goal['completedAt'] = datetime.utcnow().isoformat()
                
                # Award completion badge
                self.award_activity_badge(user_id, 'first_goal_complete')
            
            # Save updated goal
            self.table.put_item(Item=goal)
            
            return {
                'message': 'Progress updated',
                'currentDays': goal['currentDays'],
                'targetDays': goal['targetDays'],
                'completed': goal['completed']
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update goal: {str(e)}"
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
            
            return response.get('Items', [])
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
