import time
import pandas as pd
import numpy as np

CITY_DATA = { 'chicago': 'chicago.csv',
              'new york city': 'new_york_city.csv',
              'washington': 'washington.csv' }
VALID_MONTH_INPUTS = ["all","january","february","march","april","may","june"]
VALID_DAY_INPUTS = ["all","monday","tuesday","wednesday","thursday","friday","saturday","sunday"]


def get_filters():
    """
    Asks user to specify a city, month, and day to analyze.

    Returns:
        (str) city - name of the city to analyze
        (str) month - name of the month to filter by, or "all" to apply no month filter
        (str) day - name of the day of week to filter by, or "all" to apply no day filter
    """

    print('Hello! Let\'s explore some US bikeshare data!')

    # get user input for city (chicago, new york city, washington). HINT: Use a while loop to handle invalid inputs
    while(True):
        city = input("Enter the city you want to analyze(chicago,new york city,washington): ").strip().lower()
                    
        if (city in CITY_DATA):
            break

    # get user input for month (all, january, february, ... , june) 
    while(True):
        month = input("Enter the month you want to analyze(all,january,february..june): ").strip().lower()
                    
        if (month in VALID_MONTH_INPUTS):
            break

    # get user input for day of week (all, monday, tuesday, ... sunday)
    while(True):
        day = input("Enter the day of week you want to analyze(all,monday,tuesday,..sunday): ").strip().lower()
                    
        if(day in VALID_DAY_INPUTS):
            break

    print('-'*40)
    return city, month, day


def load_data(city, month, day):
    """
    Loads data for the specified city and filters by month and day if applicable.

    Args:
        (str) city - name of the city to analyze
        (str) month - name of the month to filter by, or "all" to apply no month filter
        (str) day - name of the day of week to filter by, or "all" to apply no day filter
    Returns:
        df - Pandas DataFrame containing city data filtered by month and day
    """
    df = pd.read_csv(CITY_DATA[city])
    df['Start Time'] = pd.to_datetime(df['Start Time'])
    df['month'] = df['Start Time'].dt.month
    df['weekday'] = df['Start Time'].dt.weekday_name

    if month != "all":
        # Note since all is at position 0, the months will be from index 1 and that is perfect
        df = df[df['month']==VALID_MONTH_INPUTS.index(month)]
    
    if day != "all":
        df = df[df['weekday']==day.title()]

    return df

def show_sample(df):
    while(True):
        response = input("Do you want to see a sample of the data?(Y/N): ").strip().lower()
        if(response[0]=='y' or response[0]=='n'):
            break
    if(response[0]=='y'):
        pd.set_option('display.max_columns', 1000)
        print(df.head())
        input("Press Enter key to see the statistics")
    print('-'*40)


def time_stats(df):
    """Displays statistics on the most frequent times of travel."""

    print('\nCalculating The Most Frequent Times of Travel...\n')
    start_time = time.time()

    # display the most common month
    print("The most common month in the data is {}".format(
        VALID_MONTH_INPUTS[df["month"].mode()[0]].title()))


    # display the most common day of week
    print("The most common day in the data is {}".format(
        df['weekday'].mode()[0]))

    # display the most common start hour
    df['Start Hour'] = df['Start Time'].dt.hour
    print("The most common start hour in the data is {}".format(
        df["Start Hour"].mode()[0]))


    print("\nThis took %s seconds." % (time.time() - start_time))
    print('-'*40)


def station_stats(df):
    """Displays statistics on the most popular stations and trip."""

    print('\nCalculating The Most Popular Stations and Trip...\n')
    start_time = time.time()

    # display most commonly used start station
    print("The most commonly used start station is {}".format(
        df["Start Station"].mode()[0]))


    # display most commonly used end station
    print("The most commonly used end station is {}".format(
        df["End Station"].mode()[0]))


    # display most frequent combination of start station and end station trip
    se_df = df.groupby(["Start Station","End Station"]).size().reset_index(
        name='count').sort_values('count',ascending=False)
    print("The most frequent combination of start station and end station is '{}' and '{}'".format(
        se_df.iloc[0]['Start Station'],se_df.iloc[0]['End Station']))


    print("\nThis took %s seconds." % (time.time() - start_time))
    print('-'*40)


def trip_duration_stats(df):
    """Displays statistics on the total and average trip duration."""

    print('\nCalculating Trip Duration...\n')
    start_time = time.time()

    # display total travel time
    total_trip_duration = df['Trip Duration'].sum()
    print("The total trip duration was {} seconds, approximately {} days".format(
        total_trip_duration,round(total_trip_duration/86400.0,2)))


    # display mean travel time
    mean_trip_duration = df['Trip Duration'].mean()
    print("The mean travel time was {} seconds, approximately {} minutes".format(
        mean_trip_duration,round(mean_trip_duration/60.0,2)))


    print("\nThis took %s seconds." % (time.time() - start_time))
    print('-'*40)


def user_stats(df):
    """Displays statistics on bikeshare users."""

    print('\nCalculating User Stats...\n')
    start_time = time.time()

    # Display counts of user types
    print("The count of different user types are: ")
    for k,v in df['User Type'].value_counts().items():
        print("{} - {}".format(k,v))


    # Display counts of gender
    if('Gender' not in df.columns):
        print("The data does not have gender field")
    else:
        print("The count of different genders are: ")
        for k,v in df['Gender'].value_counts().items():
            print("{} - {}".format(k,v))

    # Display earliest, most recent, and most common year of birth
    if('Birth Year' not in df.columns):
        print("The data does not have birth year field")
    else:    
        print("The earliest year of birth among riders is : ",int(df['Birth Year'].min()))
        print("The most recent year of birth among riders is : ",int(df['Birth Year'].max()))
        print("The most common year of birth among riders is : ",int(df['Birth Year'].mode()[0]))


    print("\nThis took %s seconds." % (time.time() - start_time))
    print('-'*40)


def main():
    while True:
        city, month, day = get_filters()
        #city,month,day = ("chicago","april","tuesday")
        df = load_data(city, month, day)
        show_sample(df)
        time_stats(df)
        station_stats(df)
        trip_duration_stats(df)
        user_stats(df)

        restart = input('\nWould you like to restart? Enter yes or no.\n')
        if restart.lower() != 'yes':
            break


if __name__ == "__main__":
	main()
