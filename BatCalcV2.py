import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial
from pathlib import Path
import base64
# import pdfkit

# Importing Data
windTurbines = pd.read_csv("uswtdb_v3_1.csv")
windTurbines.fillna("")
#windTurbines.replace("",0, inplace=True)
windTurbines.rename(columns={'xlong': "lon", 'ylat': 'lat'}, inplace=True)


# Project Name
# st.title("Bat Deterrent Systems Calculator")
# st.write("This is a useful tool to quickly calculate the savings that bat deterrent solutions can result in for any")
HoursAnnual = 8760


st.sidebar.subheader("Site Selection:")
option = st.sidebar.selectbox('Select your project:', windTurbines['p_name'].unique(), index=121)

st.sidebar.subheader("Parameters for site financials:")

TBAvail = st.sidebar.slider("Time Based Availability / %", min_value=0, max_value=100, value=98)
CapFactor = st.sidebar.slider("Capacity Factor / %", min_value=0, max_value=100, value=50)
EnergyPrice = st.sidebar.slider("Energy Price / $", min_value=0, max_value=100, value=30)
PTCRate = st.sidebar.slider("PTC Rate / $", min_value=0, max_value=100, value=25)
PTCYears = st.sidebar.slider("PTC Years From Start", min_value=0, max_value=25, value=10)
ProjLifetime = st.sidebar.slider("Project Lifetime", min_value=0, max_value=25, value=25)
CurtLoss = st.sidebar.slider("Bat Curtailment Loss / %", min_value=0, max_value=15, value=2)
IntRate = st.sidebar.slider("Interest Rate / %", min_value=0, max_value=15, value=8)
BDSPrice = st.sidebar.number_input('Enter BDS Price', 11900)
InstallCost = st.sidebar.number_input('Enter Installation Price', value=1500)
NetworkingCost = st.sidebar.number_input('Enter Networking Price', value=2000)
InstallYear = st.sidebar.select_slider("Deterrent Install Year: ", options=[2021, 2022, 2023], value=2021)
TotalBDS = BDSPrice+InstallCost+NetworkingCost


dfProjectDetail = (windTurbines.loc[windTurbines["p_name"] == option])

data = pd.DataFrame(np.array([['Project Capacity (MW)', dfProjectDetail.iloc[0]['p_cap']],
                              ['Turbine Manufacturer', dfProjectDetail.iloc[0]['t_manu']],
                              ['Number of Turbines', dfProjectDetail.iloc[0]['p_tnum']],
                              ['Turbine Model', dfProjectDetail.iloc[0]['t_model']],
                              ['Turbine Capacity (MW)', int(float(dfProjectDetail.iloc[0]['t_cap'])/1000)],
                              ['Turbine Rotor Diameter (m)', int(float(dfProjectDetail.iloc[0]['t_rd']))],
                              ['Project Year', int(float(dfProjectDetail.iloc[0]['p_year']))],
                              ['State', dfProjectDetail.iloc[0]['t_state']],
                              ['County', dfProjectDetail.iloc[0]['t_county']]]),
                    columns=['Feature', 'Value'])
data.set_index('Feature', inplace=True)
data.fillna("", inplace=True)
data.replace('nan', "", inplace=True)

# Building a table of financial information

styear = data["Value"]['Project Year']
i = 0
rows = []
while i <= ProjLifetime:
    rows.append([i+int(styear), 0, 0, 0, 0, 0])
    i = i+1

ProjFinancials = pd.DataFrame(rows, columns=["Year", "Energy Production", "Curtailment Loss",
                                             "Feed In Tariff", "Deterrent Savings", "Net Savings"])
ProjFinancials["Year"] = pd.to_datetime(ProjFinancials["Year"], format='%Y')
ProjFinancials.set_index("Year", inplace=True)
ProjFinancials["Energy Production"] = int(data["Value"]['Turbine Capacity (MW)']) * (CapFactor/100)\
                                      * HoursAnnual * (TBAvail / 100)
ProjFinancials["Curtailment Loss"] = ProjFinancials["Energy Production"]*(CurtLoss/100)
ProjFinancials["Feed In Tariff"] = EnergyPrice

count = 0
while count <= PTCYears:
    ProjFinancials["Feed In Tariff"][count] = EnergyPrice+PTCRate
    count = count + 1

ProjFinancials["Annual Revenue"] = ProjFinancials["Energy Production"]*ProjFinancials["Feed In Tariff"]
ProjFinancials["Annual Curt Loss"] = ProjFinancials["Curtailment Loss"]*ProjFinancials["Feed In Tariff"]
ProjFinancials["Cummulative Revenue"] = ProjFinancials["Annual Revenue"].cumsum()
ProjFinancials["Cummulative Loss"] = ProjFinancials["Annual Curt Loss"].cumsum()
ProjFinancials["BDS Financials"] = 0
ProjFinancials["BDS Savings"] = (ProjFinancials["Curtailment Loss"])

ProjFinancials.loc[str(InstallYear-1),"Deterrent Savings"] = -TotalBDS
ProjFinancials.loc[str(InstallYear-1),"Net Savings"] = -TotalBDS

i2=0
while i2 < len(ProjFinancials.loc[str(InstallYear):]):
    ProjFinancials.loc[str(InstallYear+i2),"Net Savings"]= int(ProjFinancials.loc[str(InstallYear-1+i2),"Net Savings"])+int(ProjFinancials.loc[str(InstallYear+i2),"Annual Curt Loss"])
    i2 = i2+1

NPVRevenue = numpy_financial.npv(IntRate/100, ProjFinancials["Annual Revenue"])
NPVCurtLosses = numpy_financial.npv(IntRate/100, ProjFinancials.loc[str(InstallYear):]["Annual Curt Loss"])
img_path="NRG-LogoPNG.png"
def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded
header_html = "<img src='data:image/png;base64,{}' class='img-fluid' height='100'>".format(
    img_to_bytes("NRG-LogoPNG.png")
)


col1, col2=st.beta_columns(2)

with col1:
    st.markdown(header_html, unsafe_allow_html=True)
with col2:
    st.header('Bat Deterrent ROI Calculator')
    st.text('by NRG Systems')



st.header('Simulation for '+option+' Wind Farm')

st.subheader("Cash flows - Bat Deterrent Unit Installation")
st.area_chart(ProjFinancials.loc[str(InstallYear-1):]["Net Savings"])
st.text("Note: This figures are aproximation of savings based on inputs given by the user on the slider to the left.")
st.header("Summary of Key Stats: ")
col1, col2, col3, col4 = st.beta_columns(4)

with col1:
    st.text("Bat Deterrent Payback")
    st.subheader(str(round(float(TotalBDS) / float(ProjFinancials.loc[str(InstallYear)]["Annual Curt Loss"]),2)) + " Years")
    #st.subheader("${:,.2f}".format(float(NPVRevenue)*float(data["Value"]["Number of Turbines"])))

with col2:
    st.text("Bat Deterrent Installation /per Turbine")
    # st.subheader("TBD")
    st.subheader("${:,.2f}".format(float(TotalBDS)))

with col3:
    st.text("NPV Curtailment Losses")
    st.subheader("${:,.2f}".format(float(NPVCurtLosses)*float(data["Value"]["Number of Turbines"])))

with col4:
    st.text("NPV Curtailment Losses/Turbine")
    st.subheader("${:,.2f}".format(float(NPVCurtLosses)))

# st.header("Cumulative Loss Due to Curtailment (USD per Turbine)")
# st.line_chart(ProjFinancials[["Cummulative Loss"]])

col1, col2 = st.beta_columns(2)

with col1:
    st.header("Site Information")
    st.table(data)

with col2:
    st.header("Site Location")
    st.map(windTurbines.loc[windTurbines["p_name"] == option])

st.header("Annual Revenue and Loss Due to Curtailment (USD per Turbine)")
st.line_chart(ProjFinancials[["Annual Revenue", "Annual Curt Loss"]])

st.table(ProjFinancials)


