from src.config.reports import HSReport, CLDCReport, COM1100Report, FDSReport
from src.config.timeline import Timeline
import os
import logging
from datetime import datetime as dt
import argparse

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()

logfile = f"logs/{dt.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
if not os.path.exists("logs"):
    os.makedirs("logs")
logging.basicConfig(
    filename=logfile,
    encoding='utf-8',
    level=logging.DEBUG,
    filemode='w',
    format='%(levelname)s:%(asctime)s:[%(module)s] %(message)s'
)
logging.info("Log started")

parser = argparse.ArgumentParser(prog="Handshake Timeline Reporting",
                                 description="A script that uses data from Handshake reports to create a Timeline of all student engagements from 2019-present. With this timeline, the user has the ability to generate several other reports.")

parser.add_argument('-ar', '--add_report_output', help="specifies a list of comma separated reports you'd like to recieve outputs for",
                    nargs='*', default="CLDC, COM1100, FDS")

args = parser.parse_args()


class Driver:
    def __init__(self):
        pass

    def run(self, reports_desired: list[str] | str) -> None:

        timeline = Timeline()

        reports = ["Applications", "Appointments", "Career_Fairs", "Events", "Logins"]

        for report in reports:
            obj = HSReport(report_type=report)
            app_report = obj.content
            timeline.add_report(report=app_report, tag=report)

        timeline.add_enrollment()
        timeline.create_timeline()
        timeline.process_timeline()

        outputs=[timeline.timeline]
        paths=["outputs/timeline.csv"]

        if "CLDC" in reports_desired:
            cldc_agg, cldc_melt = CLDCReport().generate_reports(timeline=timeline.timeline)
            outputs.extend([cldc_agg, cldc_melt])
            paths.extend(["outputs/cldc_agg.csv", "outputs/cldc_melt.csv"])

        if "COM1100" in reports_desired:
            combined_agg, combined_melt = COM1100Report().generate_reports(enrollment=timeline.enrollment, timeline=timeline.timeline)
            outputs.extend([combined_agg, combined_melt])
            paths.extend(["outputs/COM1100_agg.csv", "outputs/COM1100_melt.csv"])

        if "FDS" in reports_desired:
            so_agg, so_melt = FDSReport().generate_reports(timeline=timeline.timeline)
            outputs.extend([so_agg, so_melt])
            paths.extend(["outputs/fds_agg.csv", "outputs/fds_melt.csv"])

        for output, path in zip(outputs, paths):
            print(f'{Fore.GREEN} {path} successfully saved. {Style.RESET_ALL}')
            logging.info(f"{path} saved")
            output.to_csv(path)

Driver().run(reports_desired=args.add_report_output)