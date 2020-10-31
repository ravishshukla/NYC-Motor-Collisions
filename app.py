import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATA_URL = (
"https://blob-ap-south-1-ukyez4.s3.ap-south-1.amazonaws.com/sara/0b/0b4b/0b4bc542-7c43-45db-9658-6dfcd003e0c8.bin?response-content-disposition=attachment%3B%20filename%3D%22Motor_Vehicle_Collisions_-_Crashes.csv%22&response-content-type=application%2Fvnd.ms-excel&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAI75SICYCOZ7DPWTA%2F20201031%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Date=20201031T094850Z&X-Amz-SignedHeaders=host&X-Amz-Expires=1800&X-Amz-Signature=d49e9564ce32505f82385b7a42b5bbca8f2c52830609e7e1b8a13350c5e370f7"
)

st.title("Motor Vehicle Collisions in New York City")
st.markdown("This application is a Streamlit dashboard that can be used\n to analyze motor vehicle collisions in New York City 🗽")

@st.cache(persist=True)#a decorator which inteligently uses the computated Data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows = nrows, parse_dates=[['CRASH_DATE','CRASH_TIME']])
    data.dropna(subset=['LATITUDE','LONGITUDE'],inplace= True) #if we dont drop missing values in Lat and long it will break the application, And lat and long must be specified as Columns for streamit to plot the data
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns',inplace=True)
    data.rename(columns={'crash_date_crash_time': 'date/time'}, inplace=True)
    return data


data = load_data(100000)

original_data = data


st.header("Where are the most people injured in NYC?")
injured_people = st.slider("Number of people injured in vehicle collisions", 0, 19)
st.map(data.query("injured_persons >= @injured_people")[["latitude","longitude"]].dropna(how="any")) # We add a data query to filter the data, the "how" operation if specified as "any" if any LATITUDEand LONGITUDE value is NA we drop the entire row


st.header("How many collisions have occured in a given time of the day?")
hour = st.sidebar.slider("Hour of the day for inspection.", 0, 23)
data = data[data['date/time'].dt.hour == hour] # we can use dt.hour on date/time because we've converted it to pandas datetime format, here we subset our data that the date/time column we renamed earlier is matched with the value provided by the hour slider


st.markdown("Vehicle collisions between %i:00 and %i:00" %(hour, (hour+1)%24))
midpoint = (np.average(data['latitude']), np.average(data['longitude']))

st.write(pdk.Deck(

    map_style = "mapbox://styles/mapbox/light-v9",
    initial_view_state = {              # Defineed by a dict
        "latitude" : midpoint[0],
        "longitude" : midpoint[1],
        "zoom" : 11,
        "pitch" : 50,
    },
    layers = [
        pdk.Layer(
        "HexagonLayer",
        data = data[['date/time', 'latitude', 'longitude']], # we subset the data by 3 columns date/time, LAt and long so that the, lat and lont of the specific date and time can be recovered, any other column added to the subset will break the graph
        get_position = ['longitude', 'latitude'],
        radius = 100,
        extruded = True,
        pickable = True,
        elevation_scale = 4,
        elevation_range = [0, 1000],
        ), #defined by a tuple
    ],
))

st.subheader("Breakdown by minute between %i:00 and %i:00" % (hour, (hour+1)%24))
filtered = data[
    (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour <(hour+1))
]
hist = np.histogram(filtered['date/time'].dt.minute, bins = 60, range =(0, 60))[0]
chart_data = pd.DataFrame({'minute': range(60), 'crashes':hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute','crashes'], height = 400)

st.write(fig)

st.header("Top 5 dangerous streets by affected type")

select = st.sidebar.selectbox('Afeected type of people',['Pedestrians', 'Cyclists', 'Motorists'])

if select == 'Pedestrians':
    st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name","injured_pedestrians"]].sort_values(by=["injured_pedestrians"], ascending = False).dropna(how="any")[0:5])

elif select == 'Cyclists':
    st.write(original_data.query("injured_cyclists >= 1")[["on_street_name","injured_cyclists"]].sort_values(by=["injured_cyclists"], ascending = False).dropna(how="any")[0:5])

elif select == 'Motorists':
    st.write(original_data.query("injured_motorists >= 1")[["on_street_name","injured_motorists"]].sort_values(by=["injured_motorists"], ascending = False).dropna(how="any")[0:5])


if st.checkbox("Show Raw Data", False): # we add a check bow widget (Unchecked by default)
    st.subheader('Raw Data')
    st.write(data)
