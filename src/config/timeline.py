import pandas as pd
import logging
from typing import List, Optional

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

from src.config.config import Config
from src.utils import utils

CONFIG_FILE = "src\\config\\csv.config.JSON"
colorama_init()

class Timeline(Config):
    def __init__(self, config_file: Optional[str] = CONFIG_FILE) -> None:
        super().__init__(config_file=config_file)
        self._contents = []
        self._enrollment = None
        self._timeline = None

    def add_enrollment(self, process=True) -> None:
        '''
        Function that adds enrollment attribute from configuration path to the Timeline object. Following the setting of this attribute, it also can be processed. 
        Processing includes:
            - Obtaining Year from Term Code Key
            - Setting Term Code column    
        
        Input:
            - process (bool): Boolean indicating if the user would like the enrollment to be processed. Automatically set to true.
            - Output is saved as enrollment attribute.
        '''

        df = pd.read_csv(self.config["Enrollment"]["path"], dtype=str)

        if process:
            # Rename columns for appropriate handling
            df = utils.rename_columns(df=df, config_keys=self.config["Enrollment"])

            try:
                df = df.drop_duplicates(keep="first")
                df = df.loc[df["college_year"].isin(["Freshman", "Sophomore", "Junior", "Senior"]), :]

                df["Year"] = df["term_code_key"].str[:4]
                df['Term Code'] = df["term_code_key"].str[-2:]

                seasonal_mapping = {'35':'40', '5':'10', '25':'30'}
                df["Term Code"] = df["Term Code"].replace(seasonal_mapping)
                df = df.loc[df["Term Code"].isin(['40', '10', '30']), :]

                logging.debug("enrollment processing completed")

            except Exception as e:
                logging.error("enrollment processing failed")
                raise f"enrollment processing failed {e}"

        self.enrollment = df

    def add_report(self, report: pd.DataFrame, tag: str) -> None:
        '''
        Function that appends a report dataframe to the contents attribute.

        Input:
            - report (DataFrame): Dataframe of the report you would like to append.
            - tag (str): String of report type.

        Output is appended to the contents attribute of the Timeline object.
        '''

        self._contents.append(report)
        logging.debug(f"successfully added {tag} to timeline object")

    def create_timeline(self) -> pd.DataFrame:
        '''
        Function that takes the added reports within the Timeline object's content attribute and creates a concatenated timeline of these engagement reports.

        Returns:
            - DataFrame: Dataframe of concat. engagement report
            - Sets the Timeline object's timeline attribute to this dataframe.
        
        '''
        df = pd.DataFrame({})

        try: 
            for content in self.contents:
                df = pd.concat([df, content])

            df = df.loc[:, ["Email", "Student_ID", "Date", "Event_Type"]]
        except:
            logging.error("failed to concat. all reports to timeline")
            raise "failed to concat. all reports to timeline"
        
        logging.debug(f"successfully concat. all reports to timeline")

        self.timeline = df

        return self.timeline
    
    def process_timeline(self) -> pd.DataFrame:
        '''
        Function that processes the timeline attribute of the Timeline object. Processing includes:
            - Creation of semester key based on semester term.
            - Removal of null identifiers
            - Changes typing of "Year"
            - Merges timeline with enrollment to show additional student information.

        Inputs: None

        Returns: 
            - DataFrame: Dataframe of all enrolled student timelines for students participating in some engagement type.
            - Sets Timeline object's timeline attribute to this df.
        
        '''
        value_list = [('10', "Winter")] * 4 + [('30', 'Summer')] * 4 + [('40', 'Fall')] * 4
        key_list = list(range(1, 13))
        months_2key_dict = dict(zip(key_list, value_list))

        timeline = self.timeline

        try:
            timeline["Month"] = timeline["Date"].dt.month
            timeline["Year"] = timeline["Date"].dt.year.astype("str")
            timeline["Key"] = timeline["Month"].map({key: value[0] for key, value in months_2key_dict.items()})
            timeline = timeline.loc[~timeline["Student_ID"].isnull(), :]
            self.enrollment["Year"] = self.enrollment["Year"].astype("str")

            timeline = pd.merge(self.enrollment, timeline, how="left", left_on=["Student_ID", "Year", "Term Code"], right_on=["Student_ID", "Year", "Key"])
            timeline = timeline[timeline["Event_Type"].notna()]
            timeline = timeline.sort_values(["Student_ID", "Date"], ascending=True)
            timeline["Date"] = timeline["Date"].dt.strftime('%Y%m%d')

            timeline = timeline.astype(str)

            self.timeline = timeline

            logging.debug("successfully processed timeline")
            return self.timeline
        except Exception as e:
            logging.error("error processing timeline")
            raise f"error processing timeline: {e}"

    logging.debug("Successfully processed timeline report")
    print(f'{Fore.GREEN} Timeline report successfully processed! {Style.RESET_ALL}')


    @property
    def enrollment(self) -> pd.DataFrame:
        return self._enrollment

    @enrollment.setter
    def enrollment(self, enrollment) -> None:
        self._enrollment = enrollment

    @property
    def timeline(self) -> pd.DataFrame:
        return self._timeline
    
    @timeline.setter
    def timeline(self, timeline) -> None:
        self._timeline = timeline
    
    @property
    def contents(self) -> List[pd.DataFrame]:
        return self._contents
    
    @contents.setter
    def contents(self, contents) -> None:
        self._contents = contents