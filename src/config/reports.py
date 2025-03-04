import pandas as pd
import logging

from typing import Optional
from datetime import datetime

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

from src.utils import utils
from src.config.config import Config

CONFIG_FILE = "src\\config\\csv.config.JSON"
colorama_init()

class Report(Config):
    def __init__(self, report_type: str, config_file: Optional[str] = CONFIG_FILE) -> None:
        super().__init__(config_file=config_file)
        self._report_type = report_type
        self._content = None
        self.content = self._load_file()

        self._req_col_check(req_cols=["Student_ID", "Date", "path", "Email"])
        self.content = utils.rename_columns(df=self.content, config_keys=self.config[self._report_type])
    
    def _load_file(self) -> pd.DataFrame | None:
        '''
        Attempt to load the latest file from a specified general path found in config.

        Returns: 
            - DataFrame: Dataframe of said file
        '''
        try:
            # Get the most temporally recent path
            path = utils.get_latest_file_path(self.config[self._report_type]["path"])

            # Load as df
            df = pd.read_csv(path, dtype=str)
            logging.debug(f"successfully loaded report path {self._report_type}")

            return df
        
        except Exception as e:
            print(e)
            logging.warning(f"error loading report path {self._report_type}")
            return None
    
    def _req_col_check(self, req_cols: list[str]) -> None:
        '''
        Function that checks if the configuration contains necessary required columns for report processing.

        Input:
            - req_cols(list[str]): List of strings that contain required columns for specified report.
        '''
        # Obtain columns from configuration
        cols = self.config[self.report_type].keys()

        # Check each col in the required columns to see if found in config columns
        for col in req_cols:
            if col not in cols:
                logging.error(f"required column {col} missing from {self.report_type}")
                raise(f"required column {col} missing from {self.report_type}")

        logging.debug("required column check complete")

    @property
    def content(self) -> pd.DataFrame | None:
        return self._content

    @content.setter
    def content(self, content) -> pd.DataFrame | None:
        self._content = content 

    @property
    def report_type(self) -> str:
        return self._report_type
    
    @report_type.setter
    def report_type(self, report_type) -> str:
        self._report_type = report_type

class HSReport(Report):
    def __init__(self, report_type: str, config_file: Optional[str] = CONFIG_FILE) -> None:
        super().__init__(report_type=report_type, config_file=config_file)

        self.col_typing(date_col="Date")
        self.col_type_add()

    def col_typing(self, date_col: str) -> pd.DataFrame:
        '''
        Function that converts date config to a datetime format.
        
        Input:
            - date_col (str): string of the date column desired in the configuration

        Return:
            - DataFrame: Dataframe of the content involving type changing.
        
        '''

        df = self.content

        try:
            # Convert date column to datetime format
            df[date_col] = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
            df["Year"] = df[date_col].dt.year
            df["Month"] = df[date_col].dt.month
            return df

        except Exception as e:

            logging.error(f"failed to convert date column to date type for {self._report_type}")
            raise f"failed to convert date column to date type for {self._report_type}: {e}"

    def col_type_add(self) -> None:
        ''' 
        Adds type of the engagement report to the object's content attribute.
        '''
        # Create Event_Type column based off of handshake report title
        self.content["Event_Type"] = self.report_type

class CLDCReport(Report):
    
    def __init__(self, config_file: Optional[str] = CONFIG_FILE) -> None:
        super().__init__(report_type="CLDC_Report", config_file=config_file)
        self._aggregate_df = None
        self._melt_df = None

    def generate_reports(self, timeline: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        ''' 
        Function that takes student engagement timelines and the google CLDC report of referrals and returns dataframes of student engagement timelines both aggregated and melted.
        This function has been specialized for the CLDC Referral Google Sheet shared among departments.

        Returns: tuple [Aggregate DataFrame (pd.DataFrame), Melt DataFrame (pd.DataFrame)]

            Ex: Aggregate DataFrame
            ----------------------------------------------------------------------------------------------
            |      Email        |  Applications  |  Appointments  |  Career Fairs  |  Events  |  Logins  |
            |-------------------|----------------|----------------|----------------|----------|----------|
            |  jd@oakland.edu   |       0        |        3       |        1       |     2    |    10    |
            |-------------------|----------------|----------------|----------------|----------|----------|
            |       ...         |      ...       |       ...      |       ...      |    ...   |    ...   |
            |-------------------|----------------|----------------|----------------|----------|----------|

            Ex: Melted DataFrame
            ---------------------------------------------------------------------
            |      Email        |    Student_ID    |   Event_Type   |   Count   |
            |-------------------|------------------|----------------|-----------|
            |  jd@oakland.edu   |     12345        |     Events     |     4     |
            |-------------------|------------------|----------------|-----------|
            |       ...         |       ...        |       ...      |    ...    |
            |-------------------|------------------|----------------|-----------|

        '''
        ### FOR TIMELINE REPORT 
        cldc_df = self.content

        try:
            # Only desiring students that completed their appointments
            cldc_df = cldc_df[cldc_df["Completed"] == "true"]

            # Get their codes for future usage (in case they don't have engagement following appointment)
            all_codes = set(cldc_df["Email"])
            
            # Drop duplicates based on identification (which is "Email")
            cldc_df = cldc_df.sort_values(["Email", "Date"], ascending=False).drop_duplicates(subset=["Email"], keep="first")

            # Process date
            cldc_df.loc[:, 'Date'] = cldc_df['Date'].str[4:15]
            cldc_df.loc[:, 'Date'] = pd.to_datetime(cldc_df['Date'], format='%b %d %Y').dt.strftime('%Y%m%d')
            logging.debug("processed cldc report")

        except Exception as e:
            logging.error("failed to process cldc report")
            raise f"failed to process cldc report: {e}"

        # Ensure timeline information has been processed
        if {"Email", "Student_ID", "Event_Type", "Date"}.issubset(set(timeline.columns)):
            # Only desiring specific columns which should be named according to config
            tmp_engagement = timeline.loc[:, ["Email", "Student_ID", "Event_Type", "Date"]]
        else:
            logging.error("cannot generate cldc report because one of required columns ['Email', 'Student_ID', 'Event_Type', 'Date'] is missing")
            raise "cannot generate cldc report because one of required columns ['Email', 'Student_ID', 'Event_Type', 'Date'] is missing"

        try:
            # Merge together cldc with engagement to create the timeline
            df = pd.merge(cldc_df, tmp_engagement, on="Email", how="left", suffixes=("_appt", "_eng"))

            # Filter to only get entries where date of engagement follow appointment date
            df = df[df["Date_appt"] < df["Date_eng"]]
            df = df.rename(columns={"Date_eng": "Date Engagement", "Date_appt": "Date Appointment"})

            # Clean up columns to be a set of desired columns
            des_cols = self.config[self.report_type]["desired_cols"]
            df_tl = df[df.columns.intersection(des_cols)]
            df_tl = df_tl.drop_duplicates(subset=["Student_ID", "Event_Type", "Date Engagement"])
            logging.debug("successfully merged cldc report and handshake reports to create timeline")   

        except Exception as e:
            logging.error(f"failed to merge then process cldc report and timeline: {e}")
            raise f"failed to merge then process cldc report and timeline: {e}"

        ### FOR AGGREGATE
        try:
            # Use timeline to pivot for aggregate
            df_agg = pd.pivot_table(df_tl[["Email", "Student_ID", "Event_Type"]], index=["Email", "Student_ID"], columns="Event_Type", aggfunc=len, fill_value=0)

            df_agg = df_agg.reset_index()
            df_agg.columns.name = None

            # Get students that weren't on the timeline
            missing_stu = list(all_codes - set(df_agg["Email"]))

            tmp = pd.DataFrame(columns=df_agg.columns)
            tmp["Email"] = missing_stu

            pd.set_option('future.no_silent_downcasting', True)
            tmp.fillna(value=0, inplace=True)

            # Put together aggregate with df including people that weren't on timeline
            df_agg = pd.concat([df_agg, tmp])

            logging.debug("successfully processed aggregate cldc report")

        except Exception as e:
            logging.debug(f"failed to process aggregate cldc report: {e}")
            raise f"failed to process aggregate cldc report: {e}"

        # FOR MELT
        try:
            df_melt = df_agg.melt(id_vars=["Student_ID", "Email"], value_vars=["Applications", "Appointments", "Career_Fairs", "Events", "Logins"], var_name="Event_Type", value_name="Count")

            logging.debug("successfully processed melted cldc report")

        except Exception as e:
            logging.debug(f"failed to process melted cldc report: {e}")
            raise f"failed to process melted cldc report: {e}"

        logging.debug("Successfully returned CLDC reports")
        print(f'{Fore.GREEN} CLDC Reports successfully generated! {Style.RESET_ALL}')

        return df_agg, df_melt

    @property
    def timeline(self) -> pd.DataFrame:
        return self._timeline

    @timeline.setter
    def timeline(self, timeline) -> None:
        self._timeline = timeline

    @property
    def aggregate_df(self) -> pd.DataFrame:
        return self._aggregate_df

    @aggregate_df.setter
    def aggregate_df(self, agg_df) -> None:
        self._aggregate_df = agg_df

    @property
    def melt_df(self) -> pd.DataFrame:
        return self._melt_df

    @melt_df.setter
    def melt_df(self, melt_df) -> None:
        self._melt_df = melt_df

class COM1100Report(Report):

    def __init__(self, config_file: Optional[str] = CONFIG_FILE) -> None:
        super().__init__(report_type="COM1100_Report", config_file=config_file)
        self._single_prez_aggregate_df = None
        self._single_prez_melt_df = None
        self._double_prez_aggregate_df = None
        self._double_prez_melt_df = None
        self._no_prez_aggregate_df = None
        self._no_prez_melt_df = None

    def generate_reports(self, enrollment: pd.DataFrame, timeline: pd.DataFrame) -> tuple[pd.DataFrame]:
        '''
        Takes in a timeline of student events and enrollment data and generates 4 different reports that show aggregate and melted engagement following 1+ COM 1100 presentations
        and 0 COM1100 presentations.

        Input(s):
            - enrollment(pd.DataFrame): Dataframe of student enrollment accounted for in the configuration JSON.
            - timeline(pd.DataFrame): Dataframe of student engagement over time (created from Timeline Object)

        Returns:
            - com1100_agg, com1100_melt (tuple)
                - Aggregate Format
                    -------------------------------------------------------------------------------------------------------
                    |      Student_ID     |     ...     |    Applications   |   Appointments  |  ...  |      Tag          | 
                    |---------------------|-------------|-------------------|-----------------|-------|-------------------| 
                    |        12345        |     ...     |         10        |        3        |  ...  |  No Presentation  |
                    |---------------------|-------------|-------------------|-----------------|-------|-------------------| 
                    |---------------------|-------------|-------------------|-----------------|-------|-------------------|
                    |---------------------|-------------|-------------------|-----------------|-------|-------------------|

                - Melted Format
                    -----------------------------------------------------------------------------------------------
                    |      Student_ID     |     ...     |     Event_Type    |      Count      |      Tag          |      
                    |---------------------|-------------|-------------------|-----------------|-------------------| 
                    |        12345        |     ...     |    Applications   |        3        |  No Presentation  |
                    |---------------------|-------------|-------------------|-----------------|-------------------|
                    |---------------------|-------------|-------------------|-----------------|-------------------|
                    |---------------------|-------------|-------------------|-----------------|-------------------|
        '''
        comm_df = self.content

        # Start by configuring column names
        comm_df = utils.rename_columns(df=comm_df, config_keys=self.config[self.report_type])
        comm_df = comm_df.dropna(subset="Email")

        # Formatting Date
        comm_df.loc[:, "Date"] = pd.to_datetime(comm_df["Date"], errors='coerce')
        comm_df.loc[:, "Date"] = comm_df["Date"].apply(lambda x: x.strftime('%Y%m%d'))

        # Assign different months associated semester codes
        value_list = [10] * 4 + [30] * 4 + [40] * 4
        key_list = list(range(1, 13))
        months_2key_dict = dict(zip(key_list, value_list))
        comm_df["term_code_key"] = comm_df["Date"].str[0:4] + comm_df["Date"].str[4:6].astype(int).map(months_2key_dict).astype(str)
        comm_df = comm_df.sort_values(["Email", "term_code_key"])

        # Obtain term codes from first cutoff to now.
        term_codes = []
        for year in range(2022, datetime.now().year+1):
            for code in [40, 10]:
                term_codes.append(str(year) + str(code))

        # We don't want Winter 2022.
        term_codes.remove("202210")

        # Filter only eligible term codes and Freshman
        freshman = enrollment[(enrollment["term_code_key"].isin(term_codes)) & (enrollment["college_year"] == "Freshman")]

        freshman = utils.rename_columns(df=freshman, config_keys=self.config["Enrollment"])
        freshman = freshman.dropna(subset="Student_ID")

        # Create dataframe for getting student identifiers of students that did not take COM1100
        no_com1100 = freshman[~freshman["Student_ID"].isin(comm_df["Student_ID"])]

        # Final editing of creation of the different student groups: students that attended 1 presentation, 
        # students that attended 2 presentations, and students that didn't attend any.
        com1100_no_dup = comm_df.drop_duplicates(subset="Student_ID", keep="first")
        no_com1100 = no_com1100.sort_values("term_code_key").drop_duplicates("Student_ID", keep='first')

        # Generate Reports using timeline and the student groups with required columns
        single_df_agg, single_df_melt = utils.generate_com1100_report(com1100_student_group=com1100_no_dup[["Date", "Student_ID", "college_program", "college_major", "term_code_key"]], timeline=timeline, tag="single")
        no_df_agg, no_df_melt = utils.generate_com1100_report(com1100_student_group=no_com1100[["Student_ID", "college_program", "college_major", "term_code_key"]], timeline=timeline, tag="no")

        logging.debug("Successfully returned COM1100 reports")
        print(f'{Fore.GREEN} COM1100 Reports successfully generated! {Style.RESET_ALL}')

        try:
            com1100_agg = pd.concat([single_df_agg, no_df_agg])
            com1100_melt = pd.concat([single_df_melt, no_df_melt])

            logging.debug("Successfully combined COM1100 reports")
        except:
            logging.error("Error combining com1100 reports")
            raise "Error combining com1100 reports"


        return com1100_agg, com1100_melt
        
    @property
    def enrollment(self) -> pd.DataFrame:
        return self._enrollment

    @enrollment.setter
    def enrollment(self, enrollment) -> None:
        self._enrollment = enrollment

    @property
    def single_prez_aggregate_df(self) -> pd.DataFrame:
        return self._single_prez_aggregate_df

    @single_prez_aggregate_df.setter
    def single_prez_aggregate_df(self, agg_df) -> None:
        self._single_prez_aggregate_df = agg_df

    @property
    def single_prez_melt_df(self) -> pd.DataFrame:
        return self._single_prez_melt_df

    @single_prez_melt_df.setter
    def single_prez_melt_df(self, melt_df) -> None:
        self._single_prez_melt_df = melt_df

    @property
    def double_prez_aggregate_df(self) -> pd.DataFrame:
        return self._double_prez_aggregate_df

    @double_prez_aggregate_df.setter
    def double_prez_aggregate_df(self, agg_df) -> None:
        self._double_prez_aggregate_df = agg_df

    @property
    def double_prez_melt_df(self) -> pd.DataFrame:
        return self._double_prez_melt_df

    @double_prez_melt_df.setter
    def double_prez_melt_df(self, melt_df) -> None:
        self._double_prez_melt_df = melt_df

    @property
    def no_prez_aggregate_df(self) -> pd.DataFrame:
        return self._no_prez_aggregate_df

    @no_prez_aggregate_df.setter
    def no_prez_aggregate_df(self, agg_df) -> None:
        self._no_prez_aggregate_df = agg_df

    @property
    def no_prez_melt_df(self) -> pd.DataFrame:
        return self._no_prez_melt_df

    @no_prez_melt_df.setter
    def no_prez_melt_df(self, melt_df) -> None:
        self._no_prez_melt_df = melt_df

class FDSReport(Report):

    def __init__(self, config_file: Optional[str] = CONFIG_FILE) -> None:
        super().__init__(report_type="FDS", config_file=config_file)

    def generate_reports(self, timeline: pd.DataFrame) -> pd.DataFrame:
        '''
        Takes in a timeline of student events and enrollment data and generates an aggregate report of student engagements and a melted report that is matched with their FDS outcomes.

        Input(s):
            - timeline(pd.DataFrame): Dataframe of student engagement over time (created from Timeline Object)

        Returns:
            - success_df, success_df_melt
                - Aggregate Format
                    -------------------------------------------------------------------------------------------
                    |      Student_ID     |   outcome   |    Applications   |   Appointments  |  ...  |  ...  | 
                    |---------------------|-------------|-------------------|-----------------|-------|-------| 
                    |        12345        |      1      |         10        |        3        |  ...  |  ...  |
                    |---------------------|-------------|-------------------|-----------------|-------|-------| 
                    |---------------------|-------------|-------------------|-----------------|-------|-------| 
                    |---------------------|-------------|-------------------|-----------------|-------|-------| 

                - Melted Format
                    -----------------------------------------------------------------------------------------------
                    |      Student_ID     |     college_year     |     Event_Type    |      Count      |   ...    |         
                    |---------------------|----------------------|-------------------|-----------------|----------|
                    |        12345        |       Freshman       |    Applications   |        3        |   ...    |
                    |---------------------|----------------------|-------------------|-----------------|----------|
                    |---------------------|----------------------|-------------------|-----------------|----------|
                    |---------------------|----------------------|-------------------|-----------------|----------|
        '''

        fds = self.content

        fds = utils.rename_columns(fds, config_keys=self.config["Enrollment"])

        fds["Date"] = pd.to_datetime(fds["Date"]).dt.tz_localize(None)
        fds["internships"] = fds.apply(lambda x: "1" if x["internships"] == "0" and (x["internship_emp"] != "NA" and pd.notna(x["internship_emp"])) else x["internships"], axis=1)

        fds = fds.loc[:, ~fds.columns.duplicated(keep='first')].copy()

        # Merge the timeline with the student successes. Using an outer merge because there are students with FDS that have 0 entry into the timeline
        timeline_targs = pd.merge(fds[["Student_ID", "Date"]], 
                                  timeline, how="left", on=["Student_ID"], suffixes=("_fds", "_tl"))

        # Remove any instances where a person has returned to doing events after their FDS reponse has been recorded
        timeline_targs = timeline_targs.loc[timeline_targs["Date_tl"] < timeline_targs["Date_fds"], :]

        ## AGGREGATION
        # Pivot to create columns like "Event Senior" so we can split up event and class descriptions
        student_event_counts = pd.pivot_table(timeline_targs[["Student_ID", "Event_Type", "college_year"]], 
                                              index="Student_ID", columns=["Event_Type", "college_year"], aggfunc=len)

        # Rename and clean columns
        student_event_counts.columns = [' '.join(col) for col in student_event_counts.columns]
        student_event_counts.reset_index(inplace=True)

        ## Obtain Total Counts
        # Merge timeline counts to p_status
        success_df = pd.merge(fds.loc[fds["college_level"] == "Undergraduate", ["Student_ID", "outcome", "internships", "gender", "honors_college", "gpa", "athlete_status", "urm_status",
                                                                                "FDS_year", "college_program", "college_major"]].drop_duplicates(), student_event_counts, on=["Student_ID"], how="left")

        # Ignore missing p_statuses
        success_df = success_df.dropna(subset=["outcome"])

        # Fill missing values with 0 for counts
        success_df = success_df.fillna("0")

        # Assume success involves working, continuing education, and going into the military
        success_dict = {"Employed (Unknown Hours Worked)": "1", 
                        "Employed Full-Time": "1",
                        "Employed Part-Time": "1",
                        "Not Seeking Employment": "0",
                        "Pursuing Continuing Education": "1",
                        "Seeking Employment": "0", 
                        "Serving in the Military": "1",
                        "Volunteer or Service Program": "1"}

        success_df["outcome_desc"] = success_df["outcome"]
        success_df["outcome"]= success_df["outcome"].map(success_dict)

        # Create totals counts for each event type
        events_cols = [col for col in success_df if col.startswith('Events')]
        appt_cols = [col for col in success_df if col.startswith('Appointments')]
        cf_cols = [col for col in success_df if col.startswith('Career')]
        apps_cols = [col for col in success_df if col.startswith('Applications')]
        logins_cols = [col for col in success_df if col.startswith('Logins')]
        # emp_apps_cols = [col for col in success_df if col.endswith('Employment Appointments')]

        # Create Total cols
        success_df["Total Events"] = success_df[events_cols].astype(int).sum(axis=1)
        success_df["Total Appointments"] = success_df[appt_cols].astype(int).sum(axis=1)
        success_df["Total Career Fairs"] = success_df[cf_cols].astype(int).sum(axis=1)
        success_df["Total Applications"] = success_df[apps_cols].astype(int).sum(axis=1)
        success_df["Total Logins"] = success_df[logins_cols].astype(int).sum(axis=1)

        success_df = success_df.drop_duplicates(subset="Student_ID")

        ## MELT
        id_vars = ["Student_ID", "FDS_year", "outcome", "outcome_desc", "Total Events", "Total Appointments", "Total Career Fairs", "Total Applications", "Total Logins", "internships", "gender", "honors_college", "college_major", "gpa", "athlete_status", "urm_status", "college_program"]
        value_vars = list(set(success_df.columns) - set(id_vars))

        # Create a melted df for Looker
        success_df_melt = success_df.melt(id_vars=id_vars, value_vars=value_vars, var_name="Event_Type", value_name="Count")

        # Add columns
        success_df_melt['Year'] = success_df_melt['Event_Type'].str.split(' ').str[-1]
        success_df_melt['Event_Type'] = success_df_melt['Event_Type'].str.split(' ').str[0:-1].str.join(' ')

        logging.debug("successfully created aggregate and melted FDS reports")
        print(f'{Fore.GREEN} FDS Reports successfully generated! {Style.RESET_ALL}')

        return success_df, success_df_melt