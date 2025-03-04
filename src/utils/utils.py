import pandas as pd
import logging
import glob
from typing import Optional

def rename_columns(df: pd.DataFrame, config_keys: dict) -> pd.DataFrame:
    '''
    Takes a dataframe and configuration dictionary and renames specified dataframe columns according to the configuration.

    Inputs:
        - df (DataFrame): pandas dataframe object in which contains columns you would like to be renamed.
        - config_keys (dict): Dictionary for renaming columns in format:
            {"desired_column_name": {"col_name": "What original data source has the column named.", ...}}
    
    Returns:
        - df (DataFrame): pandas dataframe of original dataframe with renamed columns
    '''

    for col in config_keys:
            try:
                df = df.rename(columns={config_keys[col]["col_name"]: col})
            except:
                pass
    return df

def get_latest_file_path(path: str) -> Optional[str]:
    '''
    Takes in a designated path string with format {desired_titling}_{date}.{ext} and returns the latest path.

    Input:
        - path(str): Formatted path string

    Returns:
        - file(str): The most recent file string
    '''
    try:
        files = sorted(glob.glob(f"{path}"), reverse=True)
        return files[0] if files else None
    except Exception as e:
        logging.error(f"error retriveving files from path {path}: {e}")
        return None
    
def generate_com1100_report(com1100_student_group: pd.DataFrame, timeline: pd.DataFrame, tag: str):
    '''
    Takes in a group of students from the COM report and a timeline of all student events and returns a tuple of dataframes containing the engagement of those
    specified students groups following (or not following) a specified number of COM presentations.

    Input(s):
        - com1100_student_group(pd.DataFrame): Dataframe of containing the grouping of students of some condition.
            Ex: Students that have only been presented 1 COM 1100 presentation.
        - timeline(pd.DataFrame): Dataframe of student engagement over time (created from Timeline Object)
        - tag(str): A string of some identifier tag for the com1100_student_group

    Returns:
        - single_df_agg, single_df_melt, double_df_agg, double_df_melt, no_df_agg, no_df_melt (tuple)
            - Aggregate Format
                -------------------------------------------------------------------------------------------
                |      Student_ID     |     ...     |    Applications   |   Appointments  |  ...  |  ...  | 
                |---------------------|-------------|-------------------|-----------------|-------|-------| 
                |        12345        |     ...     |         10        |        3        |  ...  |  ...  |
                |---------------------|-------------|-------------------|-----------------|-------|-------| 
                |---------------------|-------------|-------------------|-----------------|-------|-------| 
                |---------------------|-------------|-------------------|-----------------|-------|-------| 

            - Melted Format
                ---------------------------------------------------------------------------
                |      Student_ID     |     ...     |     Event_Type    |      Count      |
                |---------------------|-------------|-------------------|-----------------|
                |        12345        |     ...     |    Applications   |        3        |
                |---------------------|-------------|-------------------|-----------------|
                |---------------------|-------------|-------------------|-----------------|
                |---------------------|-------------|-------------------|-----------------|
    '''

    com1100_timelines = pd.merge(com1100_student_group, timeline[["Student_ID", "Event_Type", "term_code_key", "Date"]], on="Student_ID", how="left", suffixes=('_prez', '_eng'))

    try:
        com1100_timelines = com1100_timelines[com1100_timelines["Date_prez"] <= com1100_timelines["Date_eng"]]
    except:
        pass

    com1100_agg = pd.pivot_table(com1100_timelines[["Student_ID", "Event_Type", "college_program", "college_major", "term_code_key"]], 
                                    index=["Student_ID", "college_program", "college_major", "term_code_key"], columns=["Event_Type"], aggfunc=len, fill_value=0)
 
    com1100_agg.reset_index(inplace=True)

    com1100_agg = com1100_agg.fillna(0)

    com1100_melt = com1100_agg.melt(id_vars=["Student_ID", "college_program", "college_major", "term_code_key"],
                        value_vars=["Applications", "Appointments", "Career_Fairs", "Events", "Logins"],
                        var_name="Event_Type", value_name="Count")

    com1100_melt.fillna(0, inplace=True)

    com1100_agg["Tag"] = tag
    com1100_melt["Tag"] = tag

    logging.debug(f"Generated COM1100 Report for {tag}")

    return com1100_agg, com1100_melt