import datetime
import os
import requests
import json
from fpdf import FPDF
import matplotlib
matplotlib.use("WebAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Current self
_VERSION_ = "1.00"

# QuestDB
QDBEP   = os.getenv("TGR_QDB_ENDPOINT", "http://localhost:9002")
qdb_url = QDBEP + "/exec"

APIEP   = os.getenv("TGR_API_ENDPOINT", "http://localhost:8080")
api_url = APIEP + "/api"

FONT    = os.getenv("TGR_FONT", "/home/pi/tgr/console/public/fonts/la-solid-900.ttf")

class PDF(FPDF):
    def header(self):
        self.add_font("la-solid-900", fname=FONT, uni=True)
        self.set_font("la-solid-900", size=50)
        self.cell(h=40, txt="\uF55F", ln=0)
        self.set_font("helvetica", "B", 22)
        self.cell(60, 40, "TGR Grow Log", 0, 0, "C")
        self.ln(20)
        self.line(10,40,240,40)
        self.ln(20)

    def footer(self):
        # Position cursor at 1.5 cm from bottom:
        self.set_y(-15)
        # Setting font: helvetica italic 8
        self.set_font("helvetica", "I", 8)
        # Printing page number:
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")


def getGrowProps():

    props = {}
    resp = requests.get(api_url + "/grow/properties")
    if resp.ok:
        props = json.loads(resp.text)["data"]

    resp = requests.get(api_url + "/system")
    if resp.ok:
        props["growspace"] = json.loads(resp.text)["data"]["controller"]["growspace"]
        props["growroom"]  = json.loads(resp.text)["data"]["controller"]["name"]

    resp = requests.get(api_url + "/tasks/log/grow")
    if resp.ok:
        props["tasks"] = json.loads(resp.text)["data"]

    resp = requests.get(api_url + "/notes")
    if resp.ok:
        props["notes"] = json.loads(resp.text)["data"]

    resp = requests.get(
        api_url + "/images",
        params={'fullpath':'yes'}
    )
    if resp.ok:
        props["images"] = json.loads(resp.text)["data"]

    return props


def plotHistory(chart):

    #print("- Plotting {} chart.".format(chart))

    ts = []

    if chart == "Temperature":
        query = "SELECT ts,avg(extemp),avg(intemp) FROM grow_sensors SAMPLE BY 15m"
        extTemp = []
        intTemp = []
        lower = 50
        upper = 90

    elif chart == "Humidity":
        query = "SELECT ts,avg(exrh),avg(inrh) FROM grow_sensors SAMPLE BY 15m"
        extRH = []
        intRH = []
        lower = 15
        upper = 70

    elif chart == "Co2":
        query = "SELECT ts,avg(exco2) FROM grow_sensors SAMPLE BY 15m"
        extCo2 = []
        lower = 400
        upper = 2000

    elif chart == "pH":
        query = "SELECT ts,avg(wph) FROM grow_sensors SAMPLE BY 15m"
        wpH = []
        lower = 0
        upper = 10

    #print("-- Creating unique datasets for each line to be plotted...")

    resp = requests.get(qdb_url, params={'query':query})

    if not resp.ok:
        print('{"error":"Cannot retrieve grow log sensor data from QuestDB service."}')
    else:
        jsonData = json.loads(resp.text.strip('\n'))

    if chart == "Temperature":
        for row in jsonData["dataset"]:
            ts.append(row[0])
            extTemp.append(row[1])
            intTemp.append(row[2])
    elif chart == "Humidity":
        for row in jsonData["dataset"]:
            ts.append(row[0])
            extRH.append(row[1])
            intRH.append(row[2])
    elif chart == "Co2":
        for row in jsonData["dataset"]:
            ts.append(row[0])
            extCo2.append(row[1])
    elif chart == "pH":
        for row in jsonData["dataset"]:
            ts.append(row[0])
            wpH.append(row[1])

    #print("-- {} records to be plotted.".format(len(ts)))
        
    #days = mdates.DayLocator()
    #hours = mdates.HourLocator()
    #minutes = mdates.MinuteLocator()
    #seconds = mdates.SecondLocator()

    fig,ax = plt.subplots(1,1)

    plt.xlabel("{}".format("Grow #9 - Chupacabra"))

    #fig.set_figwidth("6.0")

    #ax.xaxis.set_major_locator(days)
    #ax.xaxis.set_minor_locator(hours)

    ax.set_ylabel(chart)
    ax.set_xlabel("Day/Time")

    #print("-- Plotting datasets now....")

    if chart == "Temperature":
        l1,l2 = ax.plot(ts, extTemp, ts, intTemp, linewidth=0.5)

        #l1.set_label("Outside Temp")
        #l2.set_label("Inside Temp")

        #ax.legend()
        #ax.format_xdata = mdates.DateFormatter('%m-%d-%y %H:%M')

    if chart == "Humidity":
        l1,l2 = ax.plot(ts, extRH, ts, intRH, linewidth=0.5)

        #l3.set_label("Outside RH")
        #l4.set_label("Inside RH")

        #ax.legend()
        #ax.format_xdata = mdates.DateFormatter('%m-%d-%y %H:%M')

    elif chart == "Co2":
        l1 = ax.plot(ts, extCo2, linewidth=0.5)

    elif chart == "pH":
        l1 = ax.plot(ts, wpH, linewidth=0.5)

    ax.grid(True)
    ax.set_ylim(lower,upper)
    #fig.autofmt_xdate()
    #print("-- Plot completed.")

    fname = chart + "-{}".format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))
    fig.savefig(fname)

    #print("- {} chart completed.".format(chart))

    return fname


def createLogDataCharts():

    files = {}
    charts = [ "Temperature","Humidity","Co2","pH" ]

    for chart in charts:
        files[chart] = plotHistory(chart)

    return files


def createPDFdocument(files):

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Times", size=20)

    growProps = getGrowProps()

    pdf.cell(0, 10, growProps["name"], 0, 2, "C")

    pdf.set_font("Times", size=15)
    pdf.cell(100, 5, "{}".format(growProps.get("growroom")), 0, 1)
    pdf.set_font("Times", size=11)
    pdf.cell(100, 5, "Strain: {}".format(growProps.get("strain")), 0, 0)
    pdf.cell(100, 5, "Started: {}".format(growProps["veg"].get("startdate")), 0, 1)
    pdf.cell(100, 5, "Medium: {}".format(growProps.get("medium")), 0, 0)
    pdf.cell(100, 5, "Harvested: {}".format(growProps["flower"].get("enddate")), 0, 1)
    pdf.cell(100, 5, "Yield: {}".format(growProps.get("yield")), 0, 0)
    pdf.cell(100, 5, "Veg length: {}".format(growProps["veg"].get("duration")), 0, 1)
    pdf.cell(100, 5, "Dry time: {}".format(growProps.get("drytime")), 0, 0)
    pdf.cell(100, 5, "Flower length: {}".format(growProps["flower"].get("duration")), 0, 1)
    pdf.cell(100, 5, "Cure time: {}".format(growProps.get("curetime")), 0, 0)
    pdf.ln(20)
    pdf.set_font("Times", size=15)
    pdf.cell(0, 10, "Photos", 0, 1, "C")

    for f in growProps["images"]:
        pdf.image(f, w=85)
        pdf.ln(20)

    pdf.add_page()

    pdf.set_font("Times", size=15)
    pdf.cell(0, 10, "Grow Log Charts", 0, 1, "C")

    for f in files:
        pdf.image(files[f] + ".png", w=190)
        pdf.ln(20)

    pdf.add_page()

    pdf.set_font("Times", size=15)
    pdf.cell(0, 10, "Completed Tasks", 0, 1, "C")

    pdf.set_font("Times", size=11)
    for t in growProps["tasks"]:
        pdf.cell(0, 10, "{} - {}".format(t["ts"],t["task"]), 0, 1)
        pdf.ln(2)

    pdf.add_page()

    pdf.set_font("Times", size=15)
    pdf.cell(0, 10, "Notes", 0, 1, "C")

    pdf.set_font("Times", size=11)
    for n in growProps["notes"]:
        pdf.cell(0, 10, "{} - {}".format(n["ts"],n["note"]), 0, 1)
        pdf.ln(2)

    pdf.output("growlog.pdf")


if __name__ == '__main__':

    files = createLogDataCharts()

    createPDFdocument(files)
