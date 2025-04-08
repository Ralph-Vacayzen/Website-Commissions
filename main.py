import streamlit as st
import pandas as pd

st.set_page_config(page_title='Website Activity', page_icon='⚙️', layout="centered", initial_sidebar_state="auto", menu_items=None)


st.caption('VACAYZEN')
st.title('Partner Website Activity')
st.info('Partner-managed properties activity through Vacayzen websites.')

l, r = st.columns(2)

with st.expander('Uploaded Files'):
    
    file_descriptions = [
        ['Commission_Orders_Source_Lat_Long.xlsx','Vacayzen_Production > Commission_Orders_Source_Lat_Long'],
        ['Commission_Payments.xlsx','Vacayzen_Production > Commission_Payments'],
        ['PPR_Billing.csv','Partner Program Register (PPR) > Reports > Bike > Billing'],
    ]

    files = {
        'Commission_Orders_Source_Lat_Long.xlsx': None,
        'Commission_Payments.xlsx': None,
        'PPR_Billing.csv': None,
    }

    uploaded_files = st.file_uploader(
        label='Files (' + str(len(files)) + ')',
        accept_multiple_files=True
    )

    st.info('File names are **case sensitive** and **must be identical** to the file name below.')
    st.dataframe(pd.DataFrame(file_descriptions, columns=['Required File','Source Location']), hide_index=True, use_container_width=True)

if len(uploaded_files) > 0:
    for index, file in enumerate(uploaded_files):
        files[file.name] = index

    hasAllRequiredFiles = True
    missing = []

    for file in files:
        if files[file] == None:
            hasAllRequiredFiles = False
            missing.append(file)

if len(uploaded_files) > 0 and not hasAllRequiredFiles:

    for item in missing:
        st.warning('**' + item + '** is missing and required.')

elif len(uploaded_files) > 0 and hasAllRequiredFiles:
    
    orders                        = pd.read_excel(uploaded_files[files['Commission_Orders_Source_Lat_Long.xlsx']])
    payments                      = pd.read_excel(uploaded_files[files['Commission_Payments.xlsx']])
    properties                    = pd.read_csv(uploaded_files[files['PPR_Billing.csv']])
    properties['BIKE START DATE'] = pd.to_datetime(properties['BIKE START DATE'])
    properties['BIKE END DATE']   = pd.to_datetime(properties['BIKE END DATE'])
    date_range                    = pd.date_range(start=properties['BIKE START DATE'].min(), end=properties['BIKE END DATE'].max(), freq='D')
    payments.Datetime             = pd.to_datetime(payments.Datetime).dt.normalize()
    payments                      = payments[payments.Datetime.isin(date_range)]
    period_start                  = properties['BIKE START DATE'].min().date().strftime("%m/%d/%Y")
    period_end                    = properties['BIKE END DATE'].max().date().strftime("%m/%d/%Y")

    st.subheader(f'{period_start} - {period_end}')

    sources          = st.multiselect('Source', options=orders['Source'].sort_values().unique(), default=['integraRental','shop.vacayzen.com'])
    partners         = st.multiselect('Partners', options=properties['PARTNER'].sort_values().unique(), default=['360 Blue, LLC','Callista Vacation Rentals'])
    commission_rate  = st.number_input('Commission Rate', min_value=0.0, max_value=1.0, value=0.18, step=0.01)

    for partner in partners:
        partner_properties    = properties[properties.PARTNER == partner]
        partner_properties    = partner_properties['ORDER #'].unique().tolist()
        partner_lat_longs     = orders[orders['Order'].isin(partner_properties)]
        partner_lat_longs     = partner_lat_longs.drop_duplicates(subset=['Latitude','Longitude'])
        relevant_orders       = orders[orders['Source'].isin(sources)]
        partner_orders        = pd.merge(partner_lat_longs, relevant_orders, on=['Latitude','Longitude'], how='inner')
        partner_order_numbers = partner_orders['Order_y'].unique().tolist()

        partner_payments  = payments[payments['Order'].isin(partner_order_numbers)]
        partner_payments['Taxes'] = partner_payments['Amount'] * 0.07
        partner_payments['Commissionable'] = partner_payments['Amount'] - partner_payments['Taxes']
        partner_payments['Commission'] = partner_payments['Commissionable'] * commission_rate
        partner_payments['Datetime'] = partner_payments['Datetime'].dt.date
        partner_payments = partner_payments[['Datetime','Order','Commissionable','Commission']]
        partner_payments.columns = ['Date','Order','Commissionable','Commission']

        partner_map_orders = pd.merge(partner_payments, orders, on=['Order'], how='left')
        partner_map_orders = pd.merge(partner_map_orders, partner_lat_longs, on=['Latitude','Longitude'], how='left')
        partner_map = partner_map_orders[['Latitude','Longitude']]
        partner_map = partner_map.drop_duplicates(subset=['Latitude','Longitude'])
        partner_map.columns = ['lat','lon']

        st.divider()
        st.subheader(partner)
        l, lm, rm, r = st.columns(4)
        l.metric('Properties (#)', value=round(len(partner_properties)))
        lm.metric('Booking Properties (#)', value=round(len(partner_map_orders['Order_y'].unique())))
        rm.metric('Orders (#)', value=round(len(partner_payments['Order'].unique())))
        r.metric('Commission ($)', value=round(partner_payments['Commission'].sum(),2))

        tab1, tab2 = st.tabs(['Data','Map'])

        with tab1:
            st.dataframe(partner_payments, use_container_width=True, hide_index=True)
        with tab2:
            st.map(partner_map, use_container_width=True)