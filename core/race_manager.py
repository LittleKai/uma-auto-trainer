import json
import re
import os
from typing import Dict, List, Optional, Tuple

class DateManager:
    """Manages date parsing and conversion from OCR text"""

    MONTHS = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    YEARS = ['Junior', 'Classic', 'Senior']

    @staticmethod
    def parse_year_text(year_text: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Parse year text from OCR
        Expected format: "Classic Year Late Oct" -> ClassicYearLateOct
        Special case: "Junior Year Pre-Debut" -> JuniorYearPreDebut (Day < 16)
        Returns: {'year': 'Classic', 'month': 'Oct', 'period': 'Late', 'day': 2}
        """
        for attempt in range(max_retries):
            try:
                # Remove spaces and normalize
                normalized = re.sub(r'\s+', '', year_text)

                # Special case: Check for Pre-Debut first
                pre_debut_pattern = r'(Junior|Classic|Senior)Year(Pre|pre)Debut'
                pre_debut_match = re.search(pre_debut_pattern, normalized, re.IGNORECASE)

                if pre_debut_match:
                    year = pre_debut_match.group(1).title()

                    if year in DateManager.YEARS:
                        # Pre-Debut is considered as Day < 16, let's use Day 1
                        year_index = DateManager.YEARS.index(year)
                        absolute_day = year_index * 24 + 1  # First day of the year

                        return {
                            'year': year,
                            'month': 'Pre',
                            'period': 'Debut',
                            'day': 1,
                            'absolute_day': absolute_day,
                            'month_num': 0,  # Special value for Pre-Debut
                            'is_pre_debut': True
                        }

                # Normal pattern: (Junior|Classic|Senior)Year(Early|Late)(Jan|Feb|...)
                pattern = r'(Junior|Classic|Senior)Year(Early|Late)([A-Za-z]{3})'
                match = re.search(pattern, normalized, re.IGNORECASE)

                if match:
                    year = match.group(1).title()
                    period = match.group(2).title()
                    month = match.group(3).title()

                    # Validate components
                    if year in DateManager.YEARS and month in DateManager.MONTHS:
                        day = 1 if period == 'Early' else 2

                        # Calculate absolute day (1-72)
                        year_index = DateManager.YEARS.index(year)
                        month_index = DateManager.MONTHS[month] - 1
                        absolute_day = year_index * 24 + month_index * 2 + (day - 1) + 1

                        return {
                            'year': year,
                            'month': month,
                            'period': period,
                            'day': day,
                            'absolute_day': absolute_day,
                            'month_num': DateManager.MONTHS[month],
                            'is_pre_debut': False
                        }

                print(f"[WARNING] Date parse attempt {attempt + 1} failed for: {year_text}")

            except Exception as e:
                print(f"[ERROR] Date parsing error on attempt {attempt + 1}: {e}")

        print(f"[ERROR] Failed to parse date after {max_retries} attempts: {year_text}")
        return None

    @staticmethod
    def is_restricted_period(date_info: Dict) -> bool:
        """
        Check if current date is in restricted racing period
        Restricted: Day 1-16 of each year OR Jul 1 - Aug 2 OR Pre-Debut
        """
        if not date_info:
            return True

        # Special case: Pre-Debut is always restricted
        if date_info.get('is_pre_debut', False):
            return True

        absolute_day = date_info['absolute_day']
        year_start = (DateManager.YEARS.index(date_info['year'])) * 24 + 1

        # Days 1-16 of each year
        if absolute_day <= year_start + 15:
            return True

        # Jul 1 - Aug 2 (July = month 7, August = month 8)
        month_num = date_info['month_num']
        if month_num == 7 or (month_num == 8 and date_info['day'] <= 2):
            return True

        return False

class RaceManager:
    """Manages race filtering and selection"""

    def __init__(self):
        self.races = self.load_race_data()
        self.filters = {
            'track': {'turf': True, 'dirt': True},
            'distance': {'sprint': True, 'mile': True, 'medium': True, 'long': True},
            'grade': {'g1': True, 'g2': True, 'g3': True, 'op': False, 'unknown': False}
        }

    def load_race_data(self) -> List[Dict]:
        """Load race data from JSON file"""
        try:
            race_file = os.path.join('assets', 'race_list.json')
            if os.path.exists(race_file):
                with open(race_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[WARNING] Race file not found: {race_file}")
                return []
        except Exception as e:
            print(f"[ERROR] Failed to load race data: {e}")
            return []

    def update_filters(self, filters: Dict):
        """Update race filters"""
        self.filters = filters

    def extract_race_properties(self, race: Dict) -> Dict:
        """Extract race properties for filtering"""
        track = race.get('track', '').lower()
        distance = race.get('distance', '').lower()
        grade = race.get('grade', '').lower()

        # Determine track type
        track_type = 'dirt' if 'dirt' in track else 'turf'

        # Determine distance category
        distance_type = 'sprint'
        if 'mile' in distance and 'medium' not in distance and 'long' not in distance:
            distance_type = 'mile'
        elif 'medium' in distance:
            distance_type = 'medium'
        elif 'long' in distance:
            distance_type = 'long'
        elif any(x in distance for x in ['1000', '1200', '1400']):
            distance_type = 'sprint'
        elif any(x in distance for x in ['1600', '1700', '1800']):
            distance_type = 'mile'
        elif any(x in distance for x in ['2000', '2100', '2200', '2400']):
            distance_type = 'medium'
        elif any(x in distance for x in ['2500', '2600', '3000', '3200', '3400', '3600']):
            distance_type = 'long'

        # Determine grade
        grade_type = 'unknown'
        if 'g1' in grade:
            grade_type = 'g1'
        elif 'g2' in grade:
            grade_type = 'g2'
        elif 'g3' in grade:
            grade_type = 'g3'
        elif 'op' in grade:
            grade_type = 'op'

        return {
            'track_type': track_type,
            'distance_type': distance_type,
            'grade_type': grade_type
        }

    def is_race_allowed(self, race: Dict, current_date: Dict) -> bool:
        """Check if race matches current filters and date"""
        if not current_date:
            return False

        # Pre-Debut period: no racing allowed
        if current_date.get('is_pre_debut', False):
            return False

        # Check if race matches current date
        race_year = race.get('year', '').split()[0]  # Get first word (Junior/Classic/Senior)
        race_date = race.get('date', '')

        if race_year.lower() != current_date['year'].lower():
            return False

        # Parse race date (e.g., "November 1" -> month=Nov, day=1)
        try:
            date_parts = race_date.split()
            if len(date_parts) >= 2:
                race_month = date_parts[0][:3]  # First 3 characters
                race_day = int(date_parts[1])

                if (race_month != current_date['month'] or
                        race_day != current_date['day']):
                    return False
        except:
            return False

        # Check filters
        props = self.extract_race_properties(race)

        # Check track filter
        if not self.filters['track'].get(props['track_type'], False):
            return False

        # Check distance filter
        if not self.filters['distance'].get(props['distance_type'], False):
            return False

        # Check grade filter
        if not self.filters['grade'].get(props['grade_type'], False):
            return False

        return True

    def get_available_races(self, current_date: Dict) -> List[Dict]:
        """Get all races available for current date with current filters"""
        if not current_date:
            return []

        # Check if in restricted period
        if DateManager.is_restricted_period(current_date):
            return []

        available_races = []
        for race in self.races:
            if self.is_race_allowed(race, current_date):
                available_races.append(race)

        return available_races

    def should_race_today(self, current_date: Dict) -> Tuple[bool, List[Dict]]:
        """
        Determine if should race today based on available races
        Returns: (should_race, available_races)
        """
        available_races = self.get_available_races(current_date)
        return len(available_races) > 0, available_races