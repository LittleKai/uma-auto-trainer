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
    def clean_ocr_text(text: str) -> str:
        """
        Clean OCR text by removing special characters and normalizing
        Also fix common OCR mistakes
        """
        # Remove common OCR artifacts and special characters
        cleaned = re.sub(r'[\\\/\|_\-\+\=\[\]{}()<>~`!@#$%^&*]', '', text)
        # Remove extra spaces
        cleaned = re.sub(r'\s+', '', cleaned)

        # Fix common OCR mistakes
        ocr_fixes = {
            'jLate': 'Late',
            'jEarly': 'Early',
            'Earlv': 'Early',
            'Latv': 'Late',
            'Eary': 'Early',
            'Lat': 'Late',
            'Eariy': 'Early',
            'Lale': 'Late',
            'Classiv': 'Classic',
            'Clasic': 'Classic',
            'Ciassic': 'Classic',
            'Glassic': 'Classic',
            'Senlor': 'Senior',
            'Senor': 'Senior',
            'Junlor': 'Junior',
            'Yunior': 'Junior',
            'Seniom': 'Senior',
            'Yean': 'Year',
            'pul': 'Jul'
        }

        for mistake, correction in ocr_fixes.items():
            cleaned = cleaned.replace(mistake, correction)

        return cleaned

    @staticmethod
    def parse_year_text(year_text: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Parse year text from OCR with improved cleaning and error handling
        Expected format: "Classic Year Late Oct" -> ClassicYearLateOct
        Special case: "Junior Year Pre-Debut" -> JuniorYearPreDebut (Day < 16)
        Special case: "FinaleSeason" -> End of career
        Returns: {'year': 'Classic', 'month': 'Oct', 'period': 'Late', 'day': 2}
        """
        print(f"[DEBUG] Original OCR text: '{year_text}'")

        # Special case: Check for Finale Season first
        cleaned_text = DateManager.clean_ocr_text(year_text)
        if 'finale' in cleaned_text.lower() or 'finalseason' in cleaned_text.lower():
            print(f"[INFO] Finale Season detected! Career completed.")
            return {
                'year': 'Finale',
                'month': 'Season',
                'period': 'End',
                'day': 1,
                'absolute_day': 73,  # Beyond normal career
                'month_num': 13,  # Special value
                'is_pre_debut': False,
                'is_finale': True
            }

        for attempt in range(max_retries):
            try:
                # Clean the OCR text first
                cleaned_text = DateManager.clean_ocr_text(year_text)
                print(f"[DEBUG] Cleaned OCR text (attempt {attempt + 1}): '{cleaned_text}'")

                # Special case: Check for Pre-Debut first
                pre_debut_pattern = r'(Junior|Classic|Senior)Year(Pre|pre)Debut'
                pre_debut_match = re.search(pre_debut_pattern, cleaned_text, re.IGNORECASE)

                if pre_debut_match:
                    year = pre_debut_match.group(1).title()

                    if year in DateManager.YEARS:
                        # Pre-Debut is considered as Day < 16, let's use Day 1
                        year_index = DateManager.YEARS.index(year)
                        absolute_day = year_index * 24 + 1  # First day of the year

                        result = {
                            'year': year,
                            'month': 'Pre',
                            'period': 'Debut',
                            'day': 1,
                            'absolute_day': absolute_day,
                            'month_num': 0,  # Special value for Pre-Debut
                            'is_pre_debut': True,
                            'is_finale': False
                        }

                        print(f"[DEBUG] Pre-Debut successfully parsed: {result}")
                        return result

                # Normal pattern: (Junior|Classic|Senior)Year(Early|Late)(Jan|Feb|...)
                pattern = r'(Junior|Classic|Senior)Year(Early|Late)([A-Za-z]{3})'
                match = re.search(pattern, cleaned_text, re.IGNORECASE)

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

                        result = {
                            'year': year,
                            'month': month,
                            'period': period,
                            'day': day,
                            'absolute_day': absolute_day,
                            'month_num': DateManager.MONTHS[month],
                            'is_pre_debut': False,
                            'is_finale': False
                        }

                        print(f"[DEBUG] Successfully parsed: {result}")
                        print(f"[DEBUG] Date details: {year} {month} {period} = Day {absolute_day}/72, Month #{DateManager.MONTHS[month]}")
                        return result

                print(f"[WARNING] Date parse attempt {attempt + 1} failed for: '{year_text}' -> '{cleaned_text}'")

            except Exception as e:
                print(f"[ERROR] Date parsing error on attempt {attempt + 1}: {e}")

        # If all attempts fail, try to give a more helpful error message
        print(f"[ERROR] Failed to parse date after {max_retries} attempts: '{year_text}'")

        # Instead of raising exception immediately, try one more fallback approach
        try:
            # Emergency fallback - try to extract any recognizable parts
            cleaned_emergency = DateManager.clean_ocr_text(year_text).lower()

            # Try to find year
            year_found = None
            for year_name in DateManager.YEARS:
                if year_name.lower() in cleaned_emergency:
                    year_found = year_name
                    break

            # Try to find month
            month_found = None
            for month_name in DateManager.MONTHS:
                if month_name.lower() in cleaned_emergency:
                    month_found = month_name
                    break

            # Try to find period
            period_found = 'Early'  # Default
            if 'late' in cleaned_emergency:
                period_found = 'Late'

            if year_found and month_found:
                print(f"[INFO] Emergency fallback parsing successful: {year_found} {period_found} {month_found}")

                day = 1 if period_found == 'Early' else 2
                year_index = DateManager.YEARS.index(year_found)
                month_index = DateManager.MONTHS[month_found] - 1
                absolute_day = year_index * 24 + month_index * 2 + (day - 1) + 1

                result = {
                    'year': year_found,
                    'month': month_found,
                    'period': period_found,
                    'day': day,
                    'absolute_day': absolute_day,
                    'month_num': DateManager.MONTHS[month_found],
                    'is_pre_debut': False,
                    'is_finale': False
                }

                print(f"[DEBUG] Emergency fallback result: {result}")
                print(f"[DEBUG] Fallback date details: {year_found} {month_found} {period_found} = Day {absolute_day}/72, Month #{DateManager.MONTHS[month_found]}")
                return result

        except Exception as e:
            print(f"[ERROR] Emergency fallback also failed: {e}")

        print(f"[CRITICAL] All parsing methods failed for: '{year_text}'")
        return None

    @staticmethod
    def is_restricted_period(date_info: Dict) -> bool:
        """
        Check if current date is in restricted racing period
        Restricted: Day 1-16 of ENTIRE CAREER OR Jul 1 - Aug 2 OR Pre-Debut
        """
        if not date_info:
            return True

        # Special case: Pre-Debut is always restricted
        if date_info.get('is_pre_debut', False):
            return True

        absolute_day = date_info['absolute_day']

        # Days 1-16 of ENTIRE CAREER (absolute days 1-16)
        if absolute_day <= 16:
            return True

        # Jul 1 - Aug 2 (July = month 7, August = month 8)
        month_num = date_info.get('month_num', 0)

        # DEBUG: Print month checking
        print(f"[DEBUG] Checking restricted period: Month #{month_num} ({'Jul' if month_num == 7 else 'Aug' if month_num == 8 else date_info.get('month', 'Unknown')})")

        if month_num == 7 or (month_num == 8 and date_info['day'] <= 2):
            print(f"[DEBUG] July-August restriction triggered: Month {month_num}, Day {date_info.get('day', 'Unknown')}")
            return True

        print(f"[DEBUG] Not in restricted period")
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

    def get_grade_priority(self, grade: str) -> int:
        """Get grade priority for sorting (lower number = higher priority)"""
        priority_map = {'g1': 1, 'g2': 2, 'g3': 3, 'op': 4, 'unknown': 5}
        return priority_map.get(grade.lower(), 6)

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

        # Sort by grade priority (G1 first, then G2, etc.)
        available_races.sort(key=lambda x: self.get_grade_priority(
            self.extract_race_properties(x)['grade_type']
        ))

        return available_races

    def get_highest_grade_race_for_date(self, current_date: Dict) -> Optional[Dict]:
        """
        Get the highest grade race available for the current date (ignoring filters)
        Returns the race with highest grade (G1 > G2 > G3 > OP > Unknown)
        """
        if not current_date:
            return None

        # Pre-Debut period: no racing allowed
        if current_date.get('is_pre_debut', False):
            return None

        # Find all races for this date regardless of filters
        date_races = []
        for race in self.races:
            race_year = race.get('year', '').split()[0]
            race_date = race.get('date', '')

            if race_year.lower() != current_date['year'].lower():
                continue

            try:
                date_parts = race_date.split()
                if len(date_parts) >= 2:
                    race_month = date_parts[0][:3]
                    race_day = int(date_parts[1])

                    if (race_month == current_date['month'] and
                            race_day == current_date['day']):
                        date_races.append(race)
            except:
                continue

        if not date_races:
            return None

        # Sort by grade priority (G1 first, then G2, etc.)
        date_races.sort(key=lambda x: self.get_grade_priority(
            self.extract_race_properties(x)['grade_type']
        ))

        return date_races[0]  # Return highest grade race

    def get_filtered_races_for_date(self, current_date: Dict) -> List[Dict]:
        """
        Get races for current date that match the current filters
        This is used for display purposes to show which races are available with current filters
        """
        if not current_date:
            return []

        # Don't check restricted period here - let the display show what would be available
        filtered_races = []
        for race in self.races:
            race_year = race.get('year', '').split()[0]
            race_date = race.get('date', '')

            if race_year.lower() != current_date['year'].lower():
                continue

            try:
                date_parts = race_date.split()
                if len(date_parts) >= 2:
                    race_month = date_parts[0][:3]
                    race_day = int(date_parts[1])

                    if (race_month == current_date['month'] and
                            race_day == current_date['day']):

                        # Check if race matches current filters
                        props = self.extract_race_properties(race)

                        # Check track filter
                        if not self.filters['track'].get(props['track_type'], False):
                            continue

                        # Check distance filter
                        if not self.filters['distance'].get(props['distance_type'], False):
                            continue

                        # Check grade filter
                        if not self.filters['grade'].get(props['grade_type'], False):
                            continue

                        filtered_races.append(race)
            except:
                continue

        # Sort by grade priority
        filtered_races.sort(key=lambda x: self.get_grade_priority(
            self.extract_race_properties(x)['grade_type']
        ))

        return filtered_races

    def should_race_today(self, current_date: Dict) -> Tuple[bool, List[Dict]]:
        """
        Determine if should race today based on available races
        Returns: (should_race, available_races)
        """
        available_races = self.get_available_races(current_date)
        return len(available_races) > 0, available_races