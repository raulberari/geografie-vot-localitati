import pandas as pd
import os

def merge_voting_data(voting_data_file, station_locations_file, output_file):
    """
    Merge voting data with station location data and calculate vote percentages.
    
    Parameters:
    voting_data_file (str): Path to the voting data CSV file
    station_locations_file (str): Path to the station locations CSV file
    output_file (str): Path where the output CSV will be saved
    """
    print(f"Reading voting data from {voting_data_file}...")
    voting_data = pd.read_csv(voting_data_file)
    
    print(f"Reading station location data from {station_locations_file}...")
    station_locations = pd.read_csv(station_locations_file)
    
    # Display the first few rows to verify the data
    print("\nVoting data sample:")
    print(voting_data.head())
    
    print("\nStation locations sample:")
    print(station_locations.head())
    
    # Process the voting data
    # Standardize column names for merging
    voting_data_processed = voting_data.rename(columns={
        'precinct_county_name': 'county',
        'precinct_nr': 'station_number',
        'precinct_name': 'voting_station_name',
        'GEORGE-NICOLAE SIMION-voturi': 'votes_simion',
        'NICUȘOR-DANIEL DAN-voturi': 'votes_dan'
    })
    
    # Extract only needed columns from voting data
    voting_data_processed = voting_data_processed[['county', 'station_number', 'voting_station_name', 'votes_simion', 'votes_dan']]
    
    # Process station locations data
    # Since the formats of the station_number might be different, convert both to string
    voting_data_processed['station_number'] = voting_data_processed['station_number'].astype(str)
    station_locations['station_number'] = station_locations['station_number'].astype(str)
    
    # Extract only needed columns from station locations
    station_locations_processed = station_locations[['station_number', 'latitude', 'longitude', 'county']]
    
    # Some preprocessing for the county field to ensure matching
    # Standardize county names for both datasets
    voting_data_processed['county'] = voting_data_processed['county'].str.upper()
    
    # Clean up county names in station_locations to match voting_data format
    if 'county' in station_locations_processed.columns:
        # Create standardized county names
        station_locations_processed['county'] = station_locations_processed['county'].str.replace('JUDEŢUL ', '', regex=False)
        station_locations_processed['county'] = station_locations_processed['county'].str.replace('JUDEȚUL ', '', regex=False)
        station_locations_processed['county'] = station_locations_processed['county'].str.upper()
        
        # Handle special cases and diacritics
        county_mapping = {
            'ILFOV': 'ILFOV',
            'BRASOV': 'BRAȘOV',
            'MURES': 'MUREȘ',
            'TIMIS': 'TIMIȘ',
            'ARGES': 'ARGEȘ',
            'BUCURESTI': 'BUCUREŞTI',
            'NEAMT': 'NEAMȚ',
            'DAMBOVITA': 'DÂMBOVIȚA',
            'VALCEA': 'VÂLCEA',
            'BISTRITA-NASAUD': 'BISTRIȚA-NĂSĂUD',
            'MARAMURES': 'MARAMUREȘ',
            'IALOMITA': 'IALOMIȚA',
            'CARAS-SEVERIN': 'CARAȘ-SEVERIN',
            'CALARASI': 'CĂLĂRAȘI',
            'GORJ': 'GORJ',
            'BUZAU': 'BUZĂU'
        }
        
        # Apply mapping to standardize county names
        for variant, standard in county_mapping.items():
            station_locations_processed.loc[station_locations_processed['county'].str.contains(variant, case=False), 'county'] = standard
            voting_data_processed.loc[voting_data_processed['county'].str.contains(variant, case=False), 'county'] = standard
    
    print(f"\nProcessed {len(voting_data_processed)} voting data records")
    print(f"Processed {len(station_locations_processed)} station location records")
    
    # Merge datasets based on station_number and county
    print("\nMerging datasets...")
    # First try to merge on both station_number and county
    merged_data = pd.merge(
        voting_data_processed, 
        station_locations_processed,
        on=['station_number', 'county'],
        how='left',
        suffixes=('', '_loc')
    )
    
    # Check for missing locations after merge
    missing_locations = merged_data[merged_data['latitude'].isna()]
    print(f"\n{len(missing_locations)} stations missing location data after merging on station_number AND county")
    
    # if len(missing_locations) > 0:
    #     print("Trying to merge remaining stations based on station_number only...")
    #     # For records with missing locations, try to merge just on station_number
    #     stations_with_missing_loc = missing_locations['station_number'].unique()
        
    #     # Create a dataframe with only the missing locations
    #     missing_data = voting_data_processed[voting_data_processed['station_number'].isin(stations_with_missing_loc)]
        
    #     # Merge these based on station_number only
    #     secondary_merge = pd.merge(
    #         missing_data,
    #         station_locations_processed,
    #         on='station_number',
    #         how='inner'  # Only keep matches
    #     )
        
    #     # Create a dictionary mapping station numbers to their location data
    #     location_dict = {}
    #     for index, row in secondary_merge.iterrows():
    #         # Only add entries with valid latitude/longitude
    #         if not pd.isna(row['latitude']):
    #             # Use station_number as key, store lat/long as values
    #             location_dict[row['station_number']] = (row['latitude'], row['longitude'])
        
    #     # Update missing locations in the original merged dataframe
    #     filled_count = 0
    #     for idx, row in merged_data.iterrows():
    #         if pd.isna(row['latitude']) and row['station_number'] in location_dict:
    #             merged_data.loc[idx, 'latitude'] = location_dict[row['station_number']][0]
    #             merged_data.loc[idx, 'longitude'] = location_dict[row['station_number']][1]
    #             filled_count += 1
        
    #     print(f"Successfully filled location data for {filled_count} stations from secondary merge")
        
    #     # Check again for missing locations
    #     still_missing = merged_data[merged_data['latitude'].isna()]
    #     print(f"After secondary merge: {len(still_missing)} stations still missing location data")
        
    #     # Try a third approach - use numeric part of station_number for matching
    #     # This helps when formats differ (e.g., '1' vs '001')
    #     if len(still_missing) > 0:
    #         print("Attempting third matching approach with numeric station numbers...")
            
    #         # Create numeric versions of station numbers
    #         def extract_numeric(val):
    #             try:
    #                 # Extract digits only from the string
    #                 return int(''.join(filter(str.isdigit, str(val))))
    #             except:
    #                 return None
            
    #         # Add numeric versions of station numbers to both dataframes
    #         voting_data_processed['station_num'] = voting_data_processed['station_number'].apply(extract_numeric)
    #         station_locations_processed['station_num'] = station_locations_processed['station_number'].apply(extract_numeric)
            
    #         # Get stations still missing location data
    #         still_missing_stations = still_missing['station_number'].unique()
    #         missing_data_second = voting_data_processed[voting_data_processed['station_number'].isin(still_missing_stations)]
            
    #         # Create a mapping from numeric station IDs to location data
    #         numeric_location_dict = {}
    #         for index, row in station_locations_processed.iterrows():
    #             if not pd.isna(row['station_num']) and not pd.isna(row['latitude']):
    #                 # Group by county and numeric station ID
    #                 key = (row['county'], row['station_num'])
    #                 numeric_location_dict[key] = (row['latitude'], row['longitude'])
            
    #         # Update still missing locations using numeric matching
    #         third_filled_count = 0
    #         for idx, row in merged_data.iterrows():
    #             if pd.isna(row['latitude']):
    #                 # Try to find a match using numeric station number and county
    #                 station_num = extract_numeric(row['station_number'])
    #                 if station_num is not None:
    #                     key = (row['county'], station_num)
    #                     if key in numeric_location_dict:
    #                         merged_data.loc[idx, 'latitude'] = numeric_location_dict[key][0]
    #                         merged_data.loc[idx, 'longitude'] = numeric_location_dict[key][1]
    #                         third_filled_count += 1
            
    #         print(f"Successfully filled location data for {third_filled_count} additional stations using numeric matching")
            
    #         # Final check for missing locations
    #         final_missing = merged_data[merged_data['latitude'].isna()]
    #         print(f"Final count of stations missing location data: {len(final_missing)}")
    
    # Calculate percentage of Simion votes
    print("\nCalculating vote percentages...")
    merged_data['total_votes'] = merged_data['votes_simion'] + merged_data['votes_dan']
    merged_data['simion_percentage'] = (merged_data['votes_simion'] / merged_data['total_votes'] * 100).round(2)
    
    # Select and reorder final columns
    result = merged_data[[
        'county', 
        'station_number', 
        'voting_station_name', 
        'latitude', 
        'longitude', 
        'votes_dan', 
        'votes_simion', 
        'simion_percentage'
    ]]
    
    # Save the result
    print(f"\nSaving results to {output_file}...")
    result.to_csv(output_file, index=False)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total stations processed: {len(result)}")
    print(f"Stations with complete data: {len(result.dropna())}")
    print(f"Stations with missing location data: {len(result[result['latitude'].isna()])}")
    
    # Display the first few rows of the result
    print("\nFirst few rows of the result:")
    print(result.head())
    
    print(f"\nData saved to {output_file}")
    return result

# Example usage
if __name__ == "__main__":
    # Define default output file name
    default_output = "merged_voting_data.csv"
    
    # Get input file paths from user
    try:        
        voting_data_file = "election_2025_official.csv"
        station_locations_file = "romanian_voting_stations_full.csv"
        output_file = "merged_voting_stations.csv"

        # Validate file paths
        if not os.path.exists(voting_data_file):
            print(f"Error: File {voting_data_file} not found")
            exit(1)
        
        if not os.path.exists(station_locations_file):
            print(f"Error: File {station_locations_file} not found")
            exit(1)
        
        # Run the merge
        merge_voting_data(voting_data_file, station_locations_file, output_file)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()