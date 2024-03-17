# =============================================================================
# libs list
# =============================================================================
# main ones
import polars as pl
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import numpy as np
# others
import itertools
import functools
import datetime as dt


# =============================================================================
# Dashboard Config Setting
# =============================================================================
st.set_page_config(
    page_title= 'GTM Dashboard'
    , page_icon= ':chart_with_upwards_trend:'
    , layout= 'wide'
    # ,initial_sidebar_state="collapsed"
    
)

st.title(':chart_with_upwards_trend: GTM Dashboard')
st.write('The Main Go-to-Market Dashboard for a New Deposit Service in Digital Banking')
st.write('Implemented by Polars for Maximum Performance ( 10-100 faster than Pandas ) on a Single Cluster.')
st.write('Keywords: Dashboard, GTM Strategy, Python (Polars, Streamlit, Dash, Plotly)')
st.write(""" For the sake of demonstration, all the calculations are done on the spot when any change is requested.
         Note: Although it is implemented in Polars, depolyment is on a public server; so from time to time ETL could take seconds ( using Pandas would be minutes).""")
st.write("""You can zoom in/out on plots or sort data tables by each columns.""")
st.markdown('<style> div.block-container{padding-top:1rem;}</style>', unsafe_allow_html = True)


# =============================================================================
# Functions
# =============================================================================
def check_metric( func ):
    
    def wrapper( df , KPI_name , kpi_type = '€', delta_type = 'normal' ):
            
        if df.is_empty():
            # st.write('Empty')
            return 'No Record' , 'No prev. Record'
        
        # st.write('not')
        return func(df , KPI_name , kpi_type, delta_type )
        
    return wrapper
    
    
@check_metric
def metric_rep ( df , KPI_name , kpi_type = '€', delta_type = 'normal' ):
    
    val , pct = df.row(-1)
    
    val_copy , pct_copy = val , pct
    
    
    if kpi_type =='%':
        val *= 100
        
    len_val = len(f'{val:.0f}')
    m = (len_val - 1)// 3 
    r = 2 - ( (len_val -1 )%  3)
    
    if kpi_type =='#' and m == 0 :
        r = 0     

    suffix= [ '' , 'K' , 'M' ,'B'][m]
    val *= ( K_frac ** m )
    
    
    
    
    len_pct = len(f'{abs(pct):.0f}') if pct!= None else "PP"
    m_pct = (len_pct - 1)// 3 
    r_pct = 2 - ( (len_pct -1 )%  3)

    suffix_pct= [ '' , 'K' , 'M' ,'B'][m_pct]
    pct *= ( K_frac ** m_pct )

    
    title = f"{freq} {KPI_name}"
    val = f"{val:03.{r}f}{suffix}{kpi_type}"
    pct = f"{pct:+.{r_pct}f}{suffix_pct} % vs. prev. {period_names[freq_index]}"\
        if pct != None else "No prev. stat"
    delta_type = delta_type if pct!= None else "off"
    
    return  val_copy , pct_copy, [title , val, pct, delta_type]


# =============================================================================
# Data 
# =============================================================================
# st.session_state.pdf = pl.DataFrame()


# if f1 is None:
#     # show user message
#     st.session_state.pdf = pl.scan_csv('saving.csv')
#     # st.write('Please Upload Your File')
# else:

#     st.write('Your File Has Uploaded Succesfully')

    
#     file_name = f1.name
#     # st.write( ' File is {}'.format(file_name) )
#     st.session_state.pdf = pl.scan_csv( file_name)

# 
K_frac = 10**(-3)
M_frac = 10**(-6)
B_frac = 10**(-9)



    
def metric_check( df ):
    if df.is_empty():
        return df.clear(1).fill_null(0)
    else:
        return df
#
# =============================================================================
# 
# Data Prepration
# 
# =============================================================================

if 'pdf' not in st.session_state:
    st.session_state.pdf = pl.scan_csv('deposit_accounts.csv')


    # st.session_state.pdf =  st.session_state.pdf.with_columns(pl.col("population") * M_frac)
    # 
    st.session_state.pdf = st.session_state.pdf.with_columns( pl.col([ 'acc_maturity_date' , 'trxn_datetime' , 'acc_opening_date']).str.to_datetime())

    st.session_state.pdf = st.session_state.pdf.sort(pl.col('trxn_datetime'))
    st.session_state.pdf = st.session_state.pdf.with_columns(
        pl.col('trxn_datetime').dt.date().alias('date')
        , pl.col('acc_maturity_date').dt.date().alias('mdate')
    )



    st.session_state.pdf = st.session_state.pdf.with_columns(  
        pl.col('date').dt.strftime("%y-W%W").alias('week')
        , pl.col('date').dt.strftime("%y-%m").alias('month')
        , pl.col('date').dt.quarter().alias('quarter')
        , pl.col('date').dt.strftime("%Y").alias('year')
        
        , pl.col('mdate').dt.strftime("%y-W%W").alias('mweek')
        , pl.col('mdate').dt.strftime("%y-%m").alias('mmonth')
        , pl.col('mdate').dt.quarter().alias('mquarter')
        , pl.col('mdate').dt.strftime("%Y").alias('myear')
    )


    st.session_state.pdf = st.session_state.pdf.with_columns(
        pl.concat_str(
            [
                pl.col("year")
                , pl.col("quarter")
            ]
            , separator="-Q",
        ).alias('quarter')
        
        , pl.concat_str(
            [
                pl.col("myear")
                , pl.col("mquarter")
            ]
            , separator="-Q",
        ).alias('mquarter')
    )

    #

    st.session_state.pdf = st.session_state.pdf.with_columns( 
        pl.col('trxn_type').replace(
            {
                'open' : 'gain'
                ,'renew' : 'gain'
                ,'top_up' : 'gain'
                ,'mature' : 'lose'
                ,'break' : 'lose'
                ,'withdraw' : 'lose'
                , 'signup' : 'join'
                , 'reject' : 'join'
                , 'verify' : 'join'
            }
        ).alias('trxn_group')
    )


    # 

    st.session_state.pdf = st.session_state.pdf.with_columns( 
        pl.when( 
            pl.col('trxn_type') == 'renew'
            
        ).then( 
            pl.col('balance')
        ).otherwise(
            pl.col('tpv')
        ).alias('atpv') # artificial tpv, since renewal's tpv is 0
    )

    st.session_state.pdf = st.session_state.pdf.with_columns( 
        pl.when( 
            pl.col('trxn_type') == 'open'
        ).then( 
            1
        ).when( 
            pl.col('trxn_type') == 'break'
        ).then( 
            -1
        ).when( 
            pl.col('trxn_type') == 'mature'
        ).then( 
            -1
        ).otherwise(
            0
        ).alias('account_status') # artificial account value ( open and close! )
    )
    st.session_state.pdf = st.session_state.pdf.with_columns( 
        pl.col('account_status').cum_sum().over('user_id').alias('account_count')
    )
    
    st.session_state.pdf = st.session_state.pdf.with_columns( 
        pl.when( 
            ( pl.col('account_count') == 0 ) & ( pl.col('account_status') == -1 )
        ).then( 
            -1
        ).when( 
            ( pl.col('account_count') == 1 ) & ( pl.col('account_status') == 1 )
        ).then( 
            1
        ).otherwise(
            0
        ).alias('user_status') # artificial user value ( join or die! )
    )
    
    
    st.session_state.pdf = st.session_state.pdf.collect().lazy()


#

if 'time_frame' not in st.session_state:
    st.session_state.time_frame = st.session_state.pdf.select(
        pl.col( ['date','week' ,'month' , 'quarter' , 'year'] ).unique()
    )

first_day = st.session_state.pdf.select('date').min().collect().to_series().min()
last_day = st.session_state.pdf.select( 'date').max().collect().to_series().max()
duration = (last_day - first_day).days
# 

# =============================================================================
# Dashboard Inputs
# =============================================================================
period_cols= [  'quarter' , 'month' , 'week' , 'date' ]
period_names= [  'Quarter' , 'Month' , 'Week' , 'Day' ]

mperiod_cols= [ 'm'+x  for x in period_cols ]

period_prefixes = [  'Q' , 'M' , 'W', 'D' ]
period_labels = [  'Quarterly' , 'Monthly' , 'Weekly' , 'Daily' ]
period_index = { x: i for i ,x in enumerate(period_labels)}



with st.expander("Filters:"):
    
    cols = st.columns(4)
    
    
    # date_container = cols[1].container()
    # all_dates = cols[1].checkbox("Whole Period",value=1 )
    
    # if 'first_day_filter' not in st.session_state:
    #     st.session_state['first_day_filter'] = first_day
    
    # if 'last_day_filter' not in st.session_state:
    #     st.session_state['last_day_filter'] = last_day
    
    # # first_day_filter , last_day_filter = first_day , last_day
    
    # if all_dates:
    #     date_container.date_input(
    #         'Analysis Interval'
    #         , value= (first_day , last_day)
    #         , min_value= first_day
    #         ,  max_value= last_day
    #         , disabled= True)
    #     st.session_state['first_day_filter'] = first_day
    #     st.session_state['last_day_filter'] = last_day

    # else:
    #     dates = date_container.date_input(
    #         'Analysis Interval'
    #         , value= (first_day , last_day)
    #         , min_value= first_day
    #         ,  max_value= last_day
    #     )
    #     if len(dates) == 1:
    #         st.session_state.first_day_filter = dates[0]
    #     else:
    #         st.session_state.first_day_filter , st.session_state.last_day_filter = dates
    
    # analysis_duration = (st.session_state.last_day_filter - st.session_state.first_day_filter).days + 1
    # freq_condition = [187 , 63, 15 , 1]
    # freq_condition = sum([ (analysis_duration//x) > 0 for x in freq_condition]) * -1
    freq_condition = 0
    freq = cols[0].selectbox('Frequency', period_labels[freq_condition:], index= 1  )
    freq_index = period_index[freq]
    filtered_period_cols = [ period_cols[  freq_index ] ]
    
    
    # st.session_state.last_day_filter = cols[1].date_input(
    #     'Analysis Closing Date'
    #     , value=  last_day
    #     , min_value= first_day
    #     ,  max_value= last_day
    # )
    

    country_list = st.session_state.pdf.select('country').unique().collect().to_pandas()['country'].sort_values().tolist()
    location_container = cols[-3].container()
    all_countries = cols[-3].checkbox("All Locations",value=1 )
    selected_locations = []
     
    if all_countries:
        location_container.multiselect("Locations:",
             ['All'],['All'] , disabled= True)
        selected_locations = country_list
    else:
        selected_locations =  location_container.multiselect("Locations:",
            country_list)
        
    service_list = st.session_state.pdf.select('service').unique().collect().to_pandas().dropna()['service'].sort_values().tolist()
    service_container = cols[-2].container()
    all_services = cols[-2].checkbox("All Services",value=1 )
    selected_services = []
    if all_services:
        service_container.multiselect("Services:",
             ['All'],['All'] , disabled= True)
        selected_services = service_list
    
    else:
        selected_services =  service_container.multiselect("Services:",
            service_list)
        
    channel_list = st.session_state.pdf.select('channel').unique().collect().to_pandas().dropna()['channel'].sort_values().tolist()
    channel_container = cols[-1].container()
    all_channels = cols[-1].checkbox("All Channels",value=1 )
    selected_channels = []
    if all_channels:
        channel_container.multiselect("Channels:",
             ['All'],['All'] , disabled= True)
        selected_channels = channel_list
    
    else:
        selected_channels =  channel_container.multiselect("Channels:",
            channel_list)
# =============================================================================
# Appling Filters
# =============================================================================

filter_pdf = st.session_state.pdf



# filter_pdf = filter_pdf.filter( pl.col('trxn_datetime') >= st.session_state.first_day_filter )
# filter_pdf = filter_pdf.filter( pl.col('trxn_datetime') <= st.session_state.last_day_filter )

# not working with states cuase new feature extreaction is with state
if len(selected_locations) > 0:
    filter_pdf = filter_pdf.filter( pl.col('country').is_in( selected_locations))

# null is added to keep signups in the data
if len(selected_services) > 0:
    filter_pdf = filter_pdf.filter(
        pl.col('service').is_in( selected_services ) \
            | pl.col('service').is_null()
            )
if len(selected_channels) > 0:
    filter_pdf = filter_pdf.filter( pl.col('channel').is_in( selected_channels))




# =============================================================================
# Feature Extraction - locations
# =============================================================================
if 'plocations' not in st.session_state:

    st.session_state.plocations = filter_pdf.select( pl.col(['country', 'population'  ]) ).unique().cache()
    st.session_state.plocations = st.session_state.plocations.select( pl.all().sort_by('population' , descending=True) )
    st.session_state.plocations = st.session_state.plocations.with_columns( country_category = pl.lit('small'))

    st.session_state.plocations = st.session_state.plocations.with_columns(
    pl.when( pl.col('population') > 20 )
                .then(pl.lit('XBig'))
            .when( pl.col('population') > 10 )
                .then(pl.lit('Big'))
            .when( pl.col('population') > 5 )
                .then(pl.lit('Med'))
            .otherwise(pl.lit('Small'))
        .alias('country_category')
    ).rename( {'population' :'market_size'})
    st.session_state.plocations = st.session_state.plocations.with_columns( 
        pl.col('market_size').mul(M_frac).alias('market_size') 
        )

# =============================================================================
# Feature Extraction - acquisition KPIs
# =============================================================================



# if 'acq_kpis' not in st.session_state:


acq_kpis = {}
signups = filter_pdf.filter( pl.col('trxn_type').is_in( ['signup' ] ) )
cols = [   'country'  ,'channel', 'verified']

for  period in  filtered_period_cols :
    
    
    combs = itertools.chain.from_iterable(
        itertools.combinations(cols, r) 
        for r in range( len(cols)+1 , -1 , -1)
    )


    kpis = [ 
        signups.group_by( pl.col( [ *x ,period  ] ) , maintain_order = True).agg( 
            pl.col('user_id').n_unique().alias( 'U')
            , pl.col('customer_acquisition_cost').mean().alias('A_CAC')
            , (pl.col('acc_opening_date') - pl.col('trxn_datetime')).dt.total_hours().mean().alias('A_TAT')
        ) for x in combs 
    ] 
    kpis = pl.concat(kpis , how= 'diagonal')
    kpis = kpis.with_columns(pl.col(cols).fill_null('all')).sort( pl.col(   period ) )

    kpis = kpis.rename({period : 'date'})
    
    kpis = kpis.with_columns(
        pl.col([ 'date', *cols  ])
        , pl.col("U").cum_sum().over( cols ).alias("cum_U")
    )
    

    kpis = kpis.with_columns(
    pl.selectors.by_dtype(pl.NUMERIC_DTYPES)\
    .pct_change().over( cols ).mul(100).round(1)\
    .name.prefix("pct_change_") )
        
    acq_kpis[ period_labels[freq_index] ] = kpis#.sort(by = 'date').collect()

    
       
    

# =============================================================================
# Feature Extraction - transaction KPIs
# =============================================================================

# if 'trxn_kpis' not in st.session_state:

trxn_kpis = {}

cols = [   'country' , 'service' , 'trxn_group','trxn_type'   ]
trxns = filter_pdf.filter( ~ pl.col('trxn_type').is_in(['signup' ,'reject' , 'verify']) ).cache()
for  period in filtered_period_cols :
    print(period)
    print ()
    
    combs = itertools.chain.from_iterable(
        itertools.combinations(cols, r) 
        for r in range( len(cols)+1 , -1 , -1)
    )

    kpis = [ 
        trxns.group_by(  pl.col( [*x , period] ) , maintain_order = True ).agg( 
            pl.col('user_id').n_unique().alias( 'U')
            , pl.col('trxn_id').count().alias(  'T')
            , 
            pl.col('tpv').sum().alias(  'TPV')
            , pl.col('atpv').sum().alias(  'ATPV')

            , pl.col('user_status').sum().alias( 'AU')
            , pl.col('account_status').sum().alias( 'AA')
            , ( pl.col('user_status') > 0 ).sum().alias( 'U_ACT')
            , ( pl.col('user_status') < 0 ).sum().alias( 'U_DCT')
            , ( pl.col('account_status') > 0 ).sum().alias( 'A_ACT')
            , ( pl.col('account_status') < 0 ).sum().alias( 'A_DCT')
        ) for x in combs 
    ] 
    kpis = pl.concat(kpis , how= 'diagonal')
    kpis = kpis.with_columns(pl.col(cols).fill_null('all')).sort( pl.col(  period ) ) 
    kpis = kpis.rename({period : 'date'})
    
#     if period != None :
#         kpis = kpis.rename({period : 'date'})
#         kpis = kpis.sort('date')
#     else:
#         kpis = kpis.rename({'literal' : 'date'}).with_columns( pl.col('date').fill_null(0) )
    
    
    kpis = kpis.with_columns(
        pl.col([ 'date', 'service' ,'trxn_type' , 'country'  ])
        , pl.col("TPV").cum_sum().over(cols).alias("DUM")
        , pl.col('AU').cum_sum().over(cols).alias("ACTIVE_U")
        , pl.col("AA").cum_sum().over(cols).alias("ACTIVE_A")
    )
    
    kpis = kpis.with_columns(
        ( pl.col(  'DUM') / pl.col(  'ACTIVE_U') ).fill_nan(0).alias(  'DUMpC')
        # , ( pl.col(  'T') / pl.col(  'U') ).alias(  'TpU')
    #     , ( pl.col(  'cum_T') / pl.col(  'cum_U') ).alias(  'cum_TpU')
    #     , ( pl.col(  'TPV') / pl.col(  'U') ).alias(  'TPVpU')
    #     , ( pl.col(  'TPV') / pl.col(  'T') ).alias(  'TPVpT')
    #     , ( pl.col(  'DUM') / pl.col(  'U') ).alias(  'DUMpC')
    #     , ( pl.col(  'DUM') / pl.col(  'T') ).alias(  'DUMpT')
        
    )
    
    kpis = kpis.with_columns(
        pl.when( pl.col('DUMpC').is_infinite() ).then(0).otherwise(pl.col('DUMpC')).alias(  'DUMpC')
    )
    kpis = kpis.with_columns(
    pl.selectors.by_dtype(pl.NUMERIC_DTYPES)\
    .pct_change().over(cols).mul(100).round(1)\
    .name.prefix("pct_change_") )
    
    trxn_kpis[ period_labels[freq_index] ] = kpis#.sort(by = 'date').collect()

# =============================================================================
# Feature Extraction - Due KPIs
# =============================================================================

# if 'due_kpis' not in st.session_state:


due_kpis = {}

cols = [  'service' ,'trxn_type' , 'country'  ]
dues = filter_pdf.filter( ~ pl.col('trxn_type').is_in(['signup' ,'reject']) )#.sort( pl.col('mdate')).cache()

for period in filtered_period_cols:
    
    print(period)
    print ()
    mperiod = 'm' + period
    combs = itertools.chain.from_iterable(
        itertools.combinations(cols, r) 
        for r in range( len(cols)+1 , -1 , -1)
    )

    kpis = [ 
        dues.group_by(  pl.col( [ *x , mperiod, period] ) , maintain_order = True).agg( 
            pl.col('user_id').n_unique().alias( 'U')
            , pl.col('trxn_id').n_unique().alias(  'T')
            , pl.col('atpv').sum().alias(  'ATPV')
        ) for x in combs 
    ] 
    kpis = pl.concat(kpis , how= 'diagonal')
    kpis = kpis.with_columns(pl.col(cols).fill_null('all')).sort( pl.col( [mperiod , period ]) )
    kpis = kpis.rename({mperiod : 'mdate' , period : 'date'})
    
#     if period != None :
#         kpis = kpis.rename({period : 'date'})
#         kpis = kpis.sort('date')
#     else:
#         kpis = kpis.rename({'literal' : 'date'}).with_columns( pl.col('date').fill_null(0) )
    
    
    kpis = kpis.with_columns(
        pl.col([ 'mdate', 'date', *cols ])
        , pl.col("ATPV").cum_sum().over([ 'mdate' ,  *cols ]).alias("DD")#.mul(-1)
    )
    
    # kpis = kpis.with_columns(
    #     ( pl.col(  'T') / pl.col(  'U') ).alias(  'TpU')
    #     , ( pl.col(  'DD') / pl.col(  'U') ).alias(  'DDpU')
    #     , ( pl.col(  'DD') / pl.col(  'T') ).alias(  'DDpT')
    # )

    
    due_kpis[ period_labels[freq_index] ] = kpis#.sort(by = ['mdate', 'date']).collect()


# =============================================================================
# Let's Go
# =============================================================================
# if 'trxns' not in st.session_state:



trxns = trxn_kpis[freq].collect()

# if 'dues' not in st.session_state:
dues = due_kpis[freq].collect()

# if 'acqs' not in st.session_state:
acqs = acq_kpis[freq].collect()

# if len(selected_locations) > 0:
#     trxns = trxns.filter( pl.col('country').is_in( selected_locations + ['all'] ))
#     dues = dues.filter( pl.col('country').is_in( selected_locations + ['all'] ))
#     acqs = acqs.filter( pl.col('country').is_in( selected_locations + ['all'] ))

# # null is added to keep signups in the data
# if len(selected_services) > 0:
#     trxns = trxns.filter(
#         pl.col('service').is_in( selected_services + ['all']  ) \
#             | pl.col('service').is_null()
#             )
#     dues = dues.filter(
#         pl.col('service').is_in( selected_services  + ['all'] ) \
#             | pl.col('service').is_null()
#             )
#     # acqs = acqs.filter(
#     #     pl.col('service').is_in( selected_services  + ['all']  ) \
#     #         | pl.col('service').is_null()
#     #         )
    
# if len(selected_channels) > 0:
#     # trxns = trxns.filter( pl.col('channel').is_in( selected_channels + ['all'] ))
#     # dues = dues.filter( pl.col('channel').is_in( selected_channels + ['all'] ))
#     acqs = acqs.filter( pl.col('channel').is_in( selected_channels + ['all'] ))

if trxns.is_empty() or dues.is_empty():
    st.write('No Transaction Occured During This Interval.')
    st.write('Please Select Another Interval.')
else:
    title_cols = st.columns(2)
    metric_cols = st.columns(4)
    fig_cols = st.columns(2)


# =============================================================================
# North Star Metrics
# =============================================================================

    

    


    
    
    title_cols[0].title('North Star Metrics')


    trxn_data = trxns.filter( 
        (pl.col('country') == 'all' )
        & ( pl.col('service') == 'all' )
        & ( pl.col('trxn_group') == 'all' )
    )#.sort('date')
    
    
  

    trxn_last = trxn_data.filter( pl.col('date') == pl.col('date').max() )
    
    
    DUM , DUM_chng, rep_data = metric_rep(
        trxn_last.filter(
            pl.col('trxn_type') == 'all'  
        ).select( pl.col(['DUM', 'pct_change_DUM']) )
        , 'Deposits under Management'
    )
    


    metric_cols[0].metric(
        * rep_data
    )
    
    
    
    NACC , NACC_chng, rep_data = metric_rep( trxn_last.filter(
        pl.col(
            'trxn_type') == 'open'  
        ).select( pl.col(['T', 'pct_change_T']) )
        , 'Account Activation'
        , kpi_type='#'
    )
    
    
    metric_cols[1].metric(
       * rep_data
    )
    
    
    trxn_data_plot = trxns.filter( 
        (pl.col('country') == 'all' )
        & ( pl.col('trxn_type') == 'all' )
        & ( pl.col('trxn_group') == 'all' )

    )
    

    time_axis = trxn_data_plot.select( pl.col('date').unique() ).to_series().to_list()
    time_axis_sorted = sorted(time_axis) 
    
    fig = px.ecdf( trxn_data_plot.to_pandas().sort_values('date')
                  , x= 'date' , y = "TPV" 
                  , color = 'service' 
                  ,   ecdfnorm=None
                  , markers=True
                  , color_discrete_map= { 'all' : 'green' ,'Fixed14' : 'purple' , 'Flexible9' :'orange' , 'Locked14' : 'blue'}
                , category_orders = { 
                    'date' : time_axis_sorted
                }
                , title= freq + ' Deposits under Management')
    fig.for_each_yaxis(lambda y: y.update(title = '€ DUM'))
    
    
    fig_cols[0].plotly_chart(fig,use_container_width=True)
    

# =============================================================================
# Counter Metrics
# =============================================================================

    title_cols[1].title('Counter Metrics')

        
    due_data = dues.filter( 
        (pl.col('country') == 'all')
        & ( pl.col('service') == 'all')
        & ( pl.col('mdate') != pl.col('date') )
    ).unique(subset='mdate', keep="last").sort( pl.col(  ['mdate','date'] ) )
    
    cols = [  'trxn_type'  ]
    
    due_data = due_data.with_columns(
        pl.selectors.by_dtype(pl.NUMERIC_DTYPES)\
        .pct_change().over(cols).mul(100).round(1)\
        .name.prefix("pct_change_") 
        )
    

    due_last = due_data.filter( 
        pl.col('mdate') > pl.col('date').max()
        ).unique(subset='date', keep="first")
    
    DD ,DD_chng, rep_data = metric_rep( 
        due_last.filter(
            pl.col('trxn_type') == 'all'  
        ).select( pl.col(['DD', 'pct_change_DD']) )
        , 'Due Deposits'
        , delta_type = 'inverse'
    )
    
    
    # DD_chng = round(DD_chng , 1)
    
    metric_cols[2].metric(
        * rep_data
    )
     
    # 
    
    
    DACC ,DACC_chng, rep_data = metric_rep( 
        trxn_last.filter(
            pl.col('trxn_type') == 'break'  
        ).select( pl.col(['T', 'pct_change_T']))
        , 'Account Deactivation'
        , kpi_type='#'
        , delta_type = 'inverse'
    )
    
    metric_cols[3].metric(
        * rep_data
    )
    
    
    trxn_data_plot2 = trxn_data.filter( 
        pl.col('trxn_type').is_in( [ 'break', 'withdraw' , 'mature', 'renew'] )
    ).with_columns( (pl.col('ATPV').abs()).alias('pATPV') )
    
    mtime_axis = due_data.select( pl.col('mdate').unique() ).to_series().to_list()
    time_axis = trxn_data_plot2.select( pl.col('date').unique() ).to_series().to_list()
    time_axis_sorted = sorted(list( set( mtime_axis + time_axis) ))


    due_data = due_data.to_pandas()
    trxn_data_plot2 = trxn_data_plot2.to_pandas()
    
    fig = px.bar( 
        trxn_data_plot2 
        , x = 'date' 
        , y = "pATPV" 
        , color = 'trxn_type' 
       
        , category_orders = { 
            'trxn_type' : ['mature' ,'break' , 'withdraw', 'renew'] 
            , 'date' : time_axis_sorted
        }
       
        , color_discrete_map= { 
            'mature': 'black' 
            , 'break':'red' 
            , 'withdraw' :'orange'
            , 'renew' : 'green'
        }  
        , title = '{} Due Deposits & Realized Transactions'.format(freq)    
                         
    )
    fig.for_each_yaxis(lambda y: y.update(title = '€ DD'))

    
    fig.add_trace( go.Scatter(
            x = due_data.mdate
            , y = due_data.DD
            , name = 'Due Deposits'
            , mode= 'lines+markers'
            ,line=dict(color='grey')
            , stackgroup='one'
            
             
        ) )
    
    fig_cols[1].plotly_chart(fig,use_container_width=True)


# =============================================================================
# Health Metrics
# =============================================================================

    
    st.title( "Health Metrics" )
    
    health_cols = st.columns([3.5,1,1,1])


    # #####################    

    DUM = trxns

    DUM = DUM.filter( 
        (pl.col('country') != 'all')
        & (pl.col('trxn_type') == 'all')
        & ( pl.col('trxn_group') == 'all' )
        & (pl.col('service') != 'all')
        & ( pl.col('date') == pl.col('date').max() )
    ) 
    
    DUM = DUM.melt( id_vars= [ 'country' ,'service' ,'trxn_type'] , value_vars= ['DUM'] ,)
    
    
    DD = dues
    DD = DD.filter( 
        (pl.col('country') != 'all')
        & (pl.col('trxn_type') == 'all')
        & (pl.col('service') != 'all')
        & ( pl.col('mdate') == pl.col('date').max() )
    )
    # DD = DD.filter ( pl.col('date') != pl.col('date').max() )
    DD = DD.unique(subset=[ 'country' ,'service' ,'trxn_type','mdate'], keep="last")

    DD = DD.melt( id_vars= [ 'country' ,'service' ,'trxn_type'] , value_vars= ['DD'] )
    data = pl.concat([ DD , DUM])
    
    data = data.filter( pl.col('value') != 0 )
    data = data.with_columns(
        pl.when( pl.col('variable') == 'DUM').then( pl.col('value').log10())\
            .otherwise(pl.col('value').log10().mul(-1) ).alias('signed_value')
            )
    data = data.with_columns( pl.col('value') * M_frac)
    
    fig = px.treemap(
        data.to_pandas(), path= [px.Constant('Europe'),'country'  , 'service' ,'variable']
        , values = "value" 
        , color = 'signed_value'
        , color_continuous_scale='rdylgn'
        , color_continuous_midpoint= 0
        
        , title = '{} Deposits under Management & Due Deposits by Segment'.format(period_labels[freq_index])
        
        
    )
    
    fig.update(layout_coloraxis_showscale=False)
    fig.data[0].texttemplate = "%{label}<br>%{value:.2f} M€<br>%{percentRoot}"
    
    
    health_cols[0].plotly_chart(fig,use_container_width=True)



    # #####################


    health_data = trxns.filter(
        ( pl.col('date') == pl.col('date').max() )
        & (pl.col('service') == 'all')
        & (pl.col('country') == 'all')
   
    )
    # health_data.with_columns( pl.col('trxn_type').replace([ 'break' , 'mature' , 'withdraw'] , 'churn') )
    health_all = health_data.filter(
        ( pl.col('trxn_group') == 'all' ) 
        & ( pl.col('trxn_type') == 'all')
    ) 
    health_open = health_data.filter(
        ( pl.col('trxn_group') == 'all' ) 
        & ( pl.col('trxn_type') == 'open')
    ) 
    health_churn = health_data.filter(
        ( pl.col('trxn_group') == 'lose' ) 
        & ( pl.col('trxn_type') == 'all')
    ) 
    health_renew = health_data.filter(
        ( pl.col('trxn_group') == 'all' ) 
        & ( pl.col('trxn_type') == 'renew')
    ) 
    

    active_clients , active_clients_chng, ac_rep = metric_rep(
        health_all.select(['ACTIVE_U','pct_change_ACTIVE_U'])
        , 'Active Clients'
        , kpi_type= '#'
    )
    churned_clients , churned_clients_chng , cc_rep = metric_rep(
        health_churn.select(['U_DCT','pct_change_U_DCT'])
        , 'Churned Clients'
        , kpi_type= '#'
        , delta_type= 'inverse'
    )
        
    renewed_clients , renewed_clients_chng , rc_rep = metric_rep(
        health_renew.select(['U','pct_change_U'])
        , 'Retained Clients'
        , kpi_type= '#'
    )
    
    active_accounts , active_account_chng, aa_rep = metric_rep(
        health_all.select(['ACTIVE_A','pct_change_ACTIVE_A'])
        , 'Active Accounts'
        , kpi_type= '#'
    )
        
    churned_accounts , churned_account_chng, ca_rep = metric_rep(
        health_churn.select(['A_DCT','pct_change_A_DCT'])
        , 'Closed Accounts'
        , kpi_type= '#'
        , delta_type= 'inverse'
    )
        
    renewed_accounts , renewed_account_chng, ra_rep = metric_rep(
        health_renew.select(['T','pct_change_T'])
        , 'Renewed Accounts'
        , kpi_type= '#'
    )

    
    net_deposits , net_deposits_chng, nd_rep = metric_rep(
        health_all.select(['DUM','pct_change_DUM'])
        , 'Net Deposits'
    )
    
    health_churn = health_churn.with_columns(pl.col(['TPV']).mul(-1) )
    lost_deposits , lost_deposits_chng, ld_rep = metric_rep(
        health_churn.select(['TPV','pct_change_TPV'])
        , 'Lost Deposits'
        , delta_type= 'inverse'
    )
    
    renewed_deposits , renewed_deposits_chng, rd_rep = metric_rep(
        health_renew.select(['ATPV','pct_change_ATPV'])
        , 'Renewed Deposits'
    )
    
    health_cols[1].title("")
    health_cols[1].title("")
    health_cols[2].title("")
    health_cols[2].title("")
    health_cols[3].title("")
    health_cols[3].title("")
    
    health_cols[1].metric( * ac_rep )
    health_cols[1].metric( * cc_rep )
    health_cols[1].metric( * rc_rep )
    
    
    health_cols[2].metric( * aa_rep )
    health_cols[2].metric( * ca_rep )
    health_cols[2].metric( * ra_rep )
    
    health_cols[3].metric( * nd_rep )
    health_cols[3].metric( * ld_rep )
    health_cols[3].metric( * rd_rep )
    
    
# =============================================================================
# Acquisition
# =============================================================================
    

    st.title( "Acquisition Metrics" )
    
    acq_cols = st.columns([3.5 ,1,1,1])
    
    data = acqs.filter( 
        (pl.col('country') != 'all')
        & (pl.col('verified') != 'all')
        & (pl.col('channel') != 'all')
    ).with_columns( pl.col('verified').replace( { 'Yes' : 'Verified' , 'No' : 'Rejected'}))

    # data = data.with_columns( pl.col('U')* K_frac) 
    
    
    fig = px.treemap(
        data.to_pandas(), path= [px.Constant('Europe'),'country' ,'channel' , 'verified']
        , values = "U" 
        , color = 'A_CAC'
        
        , color_continuous_scale='rdylgn_r'
        ,labels=dict(
            
            market_size="Market Size (M#)"
            , A_CAC="Avg. CAC (€)"
            , U="New Users"
            , DUMpC="Depoists per Client (€)"
            , country = 'Country'
        )

        
    , title= 'Current {} Acquisitions ( & avg. customer acq. cost: A_CAC)'.format(period_names[freq_index])
    )
    # fig.data[0].customdata = data.to_pandas()['A_CAC'].tolist()

    fig.data[0].texttemplate = "%{label}<br>%{value:.0f} #<br>%{percentRoot}"
    
    
    # fig.update_traces(root_color="grey")
    fig.update_traces(legendgrouptitle_text="AA" )
    
    acq_cols[0].plotly_chart(fig,use_container_width=True)


# =============================================================================
# 
# =============================================================================
    
    acq_cols[1].title("")
    acq_cols[1].title("")
    acq_cols[2].title("")
    acq_cols[2].title("")
    acq_cols[3].title("")
    acq_cols[3].title("")
    
    acq_pivot = acqs.filter( ( pl.col('country') == 'all' ) & ( pl.col('channel') == 'all' ) )
    acq_pivot = acq_pivot.pivot(index = ['country' , 'channel' ,'date' ]  , columns = 'verified' , values = 'U').fill_null(0)

    acq_pivot = acq_pivot.with_columns(
        ( pl.col('Yes') / pl.col('all') ).alias('CR')
    )
    
    acq_pivot = acq_pivot.with_columns(
        pl.selectors.by_dtype(pl.NUMERIC_DTYPES)\
        .pct_change().over(['country' , 'channel']).mul(100).round(1)\
        .name.prefix("pct_change_") )
    
    acq_pivot = acq_pivot.filter( pl.col('date') == pl.col('date').max() )
    
    data = acqs
    
    data = data.filter( 
        ( pl.col('country') == 'all' ) 
        & ( pl.col('channel') == 'all' ) 
        & ( pl.col('date') == pl.col('date').max() )
    )
    data_verified = data.filter(
        pl.col('verified') == 'all' 
    )
    
    qualified_leads ,qualified_leads_chng, ql_rep = metric_rep(
        data_verified.select(['U' , 'pct_change_U'] )
        , 'New Qualified Leads'
        , kpi_type = '#'
    )
    A_TAT , A_TAT_chng, tat_rep = metric_rep(
        data_verified.select(['A_TAT', 'pct_change_A_TAT' ] )
        , 'avg. Turn Around Time'
        , kpi_type = 'Hours'
        , delta_type= 'inverse'
    )
    A_CAC , A_CAC_chng, cac_rep = metric_rep(
        data_verified.select(['A_CAC', 'pct_change_A_CAC'])
        , 'avg. Customer Acq. Cost'
        , delta_type= 'inverse'
    )
   
    verified_clients ,  verified_clients_chng, vc_rep = metric_rep( 
        data.filter( pl.col('verified') == 'Yes' ).select(['U' , 'pct_change_U' ])
        , 'New Clients'
        , kpi_type = '#'
    )
    
    # conversion_rate = verified_clients / qualified_leads * 100
    conversion_rate, conversion_rate_chng, crc_rep = metric_rep( 
        acq_pivot.select([ 'CR', 'pct_change_CR'])
        , 'Conversion Rate'
        , kpi_type = '%'
    )
    
    new_deposits, new_deposits_chng, nd_rep = metric_rep( 
        health_open.select('U_ACT' , 'pct_change_U_ACT' )
        , 'New Deposits'
    )


    acq_cols[1].metric( * ql_rep )
    
    acq_cols[1].metric( * tat_rep )
    acq_cols[1].metric( * cac_rep )
    
    acq_cols[2].metric( * vc_rep )
    acq_cols[2].metric( * crc_rep )
    acq_cols[3].metric( * nd_rep )
    # acq_cols[2].metric('Expected Revenue', 1,1)
    
    # acq_cols[3].metric('New Deposits', 1,1)
# metric_cols[3].metric('New Cross-Sell Accounts', 1,1)


# =============================================================================
# Expansion Streategy
# =============================================================================

    st.title( "Market Expansion Plan" )

    expansion_cols = st.columns([3.5 , 3])

    cac = acqs.filter(
        (pl.col('country') != 'all')
        & (pl.col('channel') == 'all')
        & (pl.col('verified') == 'Yes')
        # & (pl.col('date') == pl.col('date').max() )

    ).group_by( pl.col( 'country') ).agg( 
        pl.col( 'cum_U' ).last().alias('client_base')
        , pl.col( 'A_CAC' ).mean().alias('A_CAC') 
        )
    # .rename( { 'cum_U' : 'client_base'})

    dum = trxns.filter(
        (pl.col('country') != 'all')
        & (pl.col('service') == 'all')
        & (pl.col('trxn_group') == 'all')
        & (pl.col('trxn_type') == 'all')
        # & (pl.col('date') == pl.col('date').max() )

    ).unique( 
        subset= 'country', keep = 'last'
    ).select( 
        pl.col( [ 'country' ,'service' , 'DUM' , 'ACTIVE_U', 'DUMpC'] ) 
        ).rename( { 'ACTIVE_U' : 'active_clients' } )

    pops = st.session_state.plocations.collect()

    penetration = pops.join( 
        dum , on = 'country' , how = 'left').join(
            cac , on = 'country' , how = 'left')

    penetration = penetration.with_columns(
        ( pl.col('client_base').mul(K_frac) /  pl.col('market_size') ).mul(100).alias('penetration_rate'))

    penetration = penetration.drop_nulls()
    fig = px.scatter(
        
        penetration.to_pandas()
        , x = 'A_CAC'
        , y = 'DUMpC'
        , size = 'market_size'
        , text= 'country'
        , color = 'penetration_rate'
        , title= "Market Opprotunity Plot (Size: Market Size)"
        ,labels=dict(
            
            market_size="Market Size (M#)"
            , A_CAC="Avg. Customer Acq. Cost (€)"
            , peneteration_rate="Peneteration Rate"
            , DUMpC="Depoists per Client (€)"
            , country = 'Country'
        )
        # , facet_col= 'service'
        # , facet_col_wrap= 2 
        # , facet_col_spacing= 0.01
        # , facet_row_spacing= 0.03
        , height = 550
        , color_continuous_scale='rdylgn_r'
        
    )
    fig.update_layout( 
        coloraxis_colorbar={"title": 'Penetration Rate' }
    )
    fig.update_traces(textposition='top center')
    # fig.update_traces(textfont_color='black' , textfont_size = 9)
    fig.update_traces(textfont_size = 9)

    expansion_cols[0].plotly_chart(fig , use_container_width=True)

    penetration = penetration.select( 
        pl.col( [ 'country','market_size' ,'client_base' , 'active_clients' 
                , 'DUM' , 'DUMpC', 'penetration_rate' , 'A_CAC'] ) 
    )
    penetration= penetration.with_columns(
        pl.col('client_base').mul(K_frac).alias('client_base')
        , pl.col('active_clients').mul(K_frac).alias('active_clients')
        , pl.col('DUM').mul(M_frac).alias('DUM')
        , pl.col('DUMpC').mul(K_frac).alias('DUMpC')
    ).rename( { 'country' : 'Country'
               ,'market_size' : 'Market Size'
               ,'client_base' : 'Client Base'
               , 'active_clients' : 'Active Clients'
               , 'DUM'  : 'Deposits under Management'
               , 'DUMpC' : 'Deposit per Client'
               , 'penetration_rate'  : 'Penetration Rate'
               , 'A_CAC' : 'Avg. Customer Acq. Cost'
               }
                )

    f = {
        'Market Size':'{:.2f} M#'
        , 'Client Base':'{:.3f} K#'
        , 'Active Clients':'{:.3f} K#'
        , 'Deposits under Management':'{:.2f} M€'
        , 'Deposit per Client':'{:.2f} K€'
        , 'Avg. Customer Acq. Cost':'{:.2f} €'
        , 'Penetration Rate':'{:.2f} %'
        }
    expansion_cols[1].title("")
    expansion_cols[1].title("")
    expansion_cols[1].title("")
    penetration = penetration.to_pandas()
    penetration.index += 1
    expansion_cols[1].dataframe(
        penetration.style.format(f).highlight_max( 
            color = 'green', subset = ['Market Size' , 'Client Base' , 'Active Clients'] 
            ).highlight_max( 
            color = 'red' , subset = ['Penetration Rate' , 'Avg. Customer Acq. Cost' ] 
            ).highlight_max( 
            color = 'green' , subset = ['Deposits under Management' , 'Deposit per Client' ] 
            ).highlight_min( 
            color = 'red', subset = ['Market Size' , 'Client Base' , 'Active Clients'] 
            ).highlight_min( 
            color = 'green' , subset = ['Penetration Rate' , 'Avg. Customer Acq. Cost' ] 
            ).highlight_min( 
            color = 'red' , subset = ['Deposits under Management' , 'Deposit per Client' ] 
            )
        )


    # expansion_cols[1].dataframe(
    #     penetration.to_pandas().style.format(f).text_gradient( 
    #         axis = 0 , cmap = 'Blues' , subset = ['market_size' ]  , vmin = -50 , vmax = 100
    #         ).text_gradient( 
    #         axis = 0 , cmap = 'YlGn' , subset = [ 'client_base' , 'active_clients']  , vmin = -10 , vmax = 10
    #         ).text_gradient( 
    #         axis = 0 , cmap = 'RdYlGn_r' , subset = [ 'A_CAC' ]  , vmin = 5 #, vmax = 15
    #         ).text_gradient( 
    #         axis = 0 , cmap = 'RdYlGn_r' , subset = ['penetration_rate' ]  , vmin = 1  , vmax = 10
    #         ).text_gradient( 
    #         axis = 0 , cmap = 'YlGn' , subset = [ 'DUMpC' ] , vmin = -100 , vmax =200
    #         ).text_gradient( 
    #         axis = 0 , cmap = 'Greens' , subset = ['DUM' ] , vmin = -500 , vmax = 500
    #         )
    #     )



# =============================================================================
# Expansion Streategy by service type : Active Clients --> active accounts
# =============================================================================


    expansion_cols = st.columns([3.5 , 3])

    cac = acqs.filter(
        (pl.col('country') != 'all')
        & (pl.col('channel') == 'all')
        & (pl.col('verified') == 'Yes')
        # & (pl.col('date') == pl.col('date').max() )

    ).group_by( pl.col( 'country') ).agg( 
        pl.col( 'cum_U' ).last().alias('client_base')
        , pl.col( 'A_CAC' ).mean().alias('A_CAC') 
        )
    # .rename( { 'cum_U' : 'client_base'})

    dum = trxns.filter(
        (pl.col('country') != 'all')
        & (pl.col('service') != 'all')
        & (pl.col('trxn_group') == 'all')
        & (pl.col('trxn_type') == 'all')
        # & (pl.col('date') == pl.col('date').max() )

    ).unique( 
        subset= ['country' , 'service'], keep = 'last'
    ).select( 
        pl.col( [ 'country' ,'service' , 'DUM' , 'ACTIVE_A', 'DUMpC'] ) 
        ).rename( { 'ACTIVE_A' : 'active_clients' } )

    pops = st.session_state.plocations.collect()

    penetration = pops.join( 
        dum , on = 'country' , how = 'left').join(
            cac , on = 'country' , how = 'left')

    penetration = penetration.with_columns(
        ( pl.col('active_clients').mul(K_frac) /  pl.col('market_size') ).mul(100).alias('penetration_rate'))
    
    penetration = penetration.with_columns(
        ( pl.col('active_clients').mul(K_frac) /  pl.col('client_base') ).mul(100).alias('AC_CB'))
    
    penetration = penetration.drop_nulls()

    fig = px.scatter(
        
        penetration.to_pandas()
        , x = 'A_CAC'
        , y = 'DUMpC'
        , size = 'market_size'
        , text= 'country'
        , color = 'penetration_rate'
        , title= "Market Opprotunity Plot for each Service (Size: Market Size)"
        ,labels=dict(
            
            market_size="Market Size (M#)"
            , A_CAC="Avg. Customer Acq. Cost (€)"
            , peneteration_rate=" Peneteration Rate"
            , DUMpC=" Depoists per Client (€)"
            , country = 'Country'
            , service = 'Service'
        )
        , facet_col= 'service'
        # , facet_col_wrap= 2 
        , facet_col_spacing= 0.05
        # , facet_row_spacing= 0.03
        , height = 550
        # , width = 800
        , color_continuous_scale='rdylgn_r'
        
    )
    fig.update_layout( 
        coloraxis_colorbar={"title": 'Penetration Rate' }
    )
    fig.update_traces(textposition='top center')
    fig.update_traces( textfont_size = 9)
    # fig.update_traces(textfont_color='black' , textfont_size = 9)

    st.plotly_chart(fig , use_container_width=True)



# Cross-selling
    product_list = penetration.select('service').unique().to_series().sort().to_list()
    combs = [ x for x in itertools.combinations( product_list, 2) ]

    relative_data = []

    for i , x in enumerate(combs):

        a = penetration.filter(
            pl.col('service') == x[0] 
            ).select(
                  pl.all().prefix('S1_') 
            ).with_columns( pl.lit(x[0]).alias('S1') )
        b = penetration.filter(
            pl.col('service') == x[1] 
            ).select( 
                pl.all().prefix('S2_') 
            ).with_columns( pl.lit(x[1]).alias('S2') )
        c = a.join(b
            , left_on= 'S1_country'
            , right_on= 'S2_country'
        ).with_columns( pl.lit('S1(' + ') vs. S2('.join(x) + ')').alias('product_set') )
        relative_data.append(c)
    
    if len(relative_data ) == 0:
        st.write('Selected Filters Contain Not Enough Product for Cross-selling Analysis')
    else:
        relative_data = pl.concat( relative_data ) 

        fig = px.scatter(
            
            relative_data.to_pandas()
            , x = 'S1_AC_CB'
            , y = 'S2_AC_CB'
            , size = 'S1_market_size'
            , text= 'S1_country'
            , color = 'S1_A_CAC'
            , title= "Cross-sell Opprotunity Plot (Size: Market Size)"
            ,labels=dict(
                
                S1_market_size="Market Size (M#)"
                , A_CAC="Avg. Customer Acq. Cost (€)"
                , S1_AC_CB="S1 Active Clients / Client Base"
                , S2_AC_CB="S2 Active Clients / Client Base"
                , S1_country = "Country"
                , product_set = "Product Set"
            )
            , facet_col= 'product_set'
            # , facet_row= 'S1'
            # , facet_col_wrap= 2 
            , facet_col_spacing= 0.05
            , facet_row_spacing= 0.03
            , height = 550
            # , width = 800
            , color_continuous_scale= ['green' , 'yellow', 'red']
            
        )   
        fig.update_layout( 
            coloraxis_colorbar={"title": 'Customer Acq. Cost (€)' }
        )
        fig.update_traces(textposition='top center')
        fig.update_traces(textfont_size = 9)

        st.plotly_chart(fig , use_container_width=True)

        # st.dataframe( trxns.filter(
        #     ( pl.col('country')== 'Montenegro' )
        #     # & ( pl.col('service')== 'Fixed14' )
        #     # & ( pl.col('trxn_group')== 'all' )
        #     # & ( pl.col('trxn_type')== 'all' ) 
        #     )
        # )



