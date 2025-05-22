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
    voting_data_processed = voting_data_processed[['county', 'station_number', 'voting_station_name', 'uat_name', 'votes_simion', 'votes_dan']]
    
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
    
    # Calculate percentage of Simion votes for each station
    print("\nCalculating vote percentages...")
    merged_data['total_votes'] = merged_data['votes_simion'] + merged_data['votes_dan']
    merged_data['simion_percentage'] = (merged_data['votes_simion'] / merged_data['total_votes'] * 100).round(2)
    
    # Calculate UAT-level averages
    print("Calculating UAT-level averages...")
    uat_stats = merged_data.groupby(['county', 'uat_name']).agg({
        'votes_simion': 'sum',
        'votes_dan': 'sum'
    }).reset_index()
    
    # Calculate UAT average percentage
    uat_stats['uat_total_votes'] = uat_stats['votes_simion'] + uat_stats['votes_dan']
    uat_stats['uat_simion_avg_percentage'] = (uat_stats['votes_simion'] / uat_stats['uat_total_votes'] * 100).round(2)
    
    # Keep only the columns we need for merging back
    uat_averages = uat_stats[['county', 'uat_name', 'uat_simion_avg_percentage']]
    
    # Merge the UAT averages back to the main dataset
    merged_data = pd.merge(
        merged_data,
        uat_averages,
        on=['county', 'uat_name'],
        how='left'
    )
    
    # Calculate the difference between station percentage and UAT average
    print("Calculating percentage differences from UAT average...")
    merged_data['simion_vs_uat_diff'] = (merged_data['simion_percentage'] - merged_data['uat_simion_avg_percentage']).round(2)
    
    # Select and reorder final columns
    result = merged_data[[
        'county', 
        'uat_name',
        'station_number', 
        'voting_station_name', 
        'latitude', 
        'longitude', 
        'votes_dan', 
        'votes_simion', 
        'simion_percentage',
        'uat_simion_avg_percentage',
        'simion_vs_uat_diff'
    ]]
    
    # Save the result
    print(f"\nSaving results to {output_file}...")
    result.to_csv(output_file, index=False)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total stations processed: {len(result)}")
    print(f"Stations with complete data: {len(result.dropna())}")
    print(f"Stations with missing location data: {len(result[result['latitude'].isna()])}")
    print(f"Unique UATs processed: {len(result['uat_name'].unique())}")
    
    # Display the first few rows of the result
    print("\nFirst few rows of the result:")
    print(result.head())
    
    # Show some UAT-level statistics
    print("\nSample UAT averages:")
    sample_uats = result.groupby(['county', 'uat_name']).first()[['uat_simion_avg_percentage']].head(10)
    print(sample_uats)
    
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