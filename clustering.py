'''

TESTESTTEST
Functions and initation for clustering techniques of flare data.

Author: Knut Ola Dølven, knut.o.dolven@uit.no (c) 2023

FUNCTIONS:

load_flare_data: Loads the FlareHunter/ESP3 excel dataset. The excel file contains data from the
FlareHunter/ESP3 experiment. The data is stored in a pandas dataframe.
The function takes a filepath and a column identified input for the excel file
which defines the column names in the excel file. It is also possible to define
the UTM zone explicitly instead of loading it into the dataframe from the excel file.

get_distance: Calculates the distance between the points in a vector with coordinates xlocs and ylocs.
The function returns a matrix with the distances between all the points in the vector.

get_shared_area: Calculates the shared area between two circles with radius R1 and R2 and
to different origins located at x_loc and y_loc. The function returns the shared area.
Reference: Weisstein, Eric W. "Circle-Circle Intersection." From MathWorld--
A Wolfram Web Resource. http://mathworld.wolfram.com/Circle-CircleIntersection.html

get_area_of_footprint: Calculates the area of the footprint of the acoustic beam of the SB echosounder at
a specified depth. The function returns the area of the footprint.

get_close_flares: Finds all the flares that are within a certain distance of each other or shares a certain
amount of area. The function use UTM x an y or lan/lot coordinates and footprint radius
to return a list of pairs with indices of flares that are defined as close to each other
according to the closeness_param and threshold parameters. Can calculate closeness based
on distance between footprint center or the fractional (%) shared area between the footprints.

cluster_flowrate_vanilla: Clusters flares that have overlapping areas/are within a certain distance of each other
(this is done through get_close_flares) and calculates the total area and flowrate
of each cluster. The function returns a dictionary with the cluster info. Based on method described in
Veloso et al., 2015, doi: 10.1002/lom3.10024

cluster_flowrate_gridded_averaging: Calculates the total area and flowrate of a flare cluster by 
gridding the cluster area, calculating the flowrate of each grid cell for each flare in the cluster,
and averaging the flowrate of each grid cell over all the flares in the cluster. The function returns
a dictionary with the cluster info. Based on method described in the memo accompanying this script.

save_clustered_data: Creates a dataframe with clustered flares and their locations and flowrates together with
the flares that were not clustered as individual clusters. Saves the dataframe to an excel file
with path/filename filepath.

write_cluster_textfile: Writes a textfile listing all the flare observations included in 
each cluster as well as all the flare observations that were not clustered.

INITIATION:
This is where you set input parameters and runs the whole thing! :-)

'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings
import tkinter as tk
import os
#Set path to the folder where this script is located (to avoid cannot find conversion-error)
script_path = os.path.abspath(__file__)#path to script
script_dir = os.path.dirname(script_path)#path to directory
os.sys.path.append(script_dir)
import conversion as utm


################################################
################# FUNCTIONS ####################
################################################

def load_flare_data(filepath,
                    lon = None,
                    lat = None,
                    UTM_X = None,
                    UTM_Y = None,
                    UTM_zone = None,
                    Depth = None,
                    Radius = None,
                    Flowrate = None,
                    lon_user_def = None,
                    lat_user_def = None,
                    UTM_X_user_def = None,
                    UTM_Y_user_def = None,
                    UTM_zone_user_def = None,
                    Depth_user_def = None,
                    Radius_user_def = None,
                    Flowrate_user_def = None):
    '''
    Loads the FlareHunter/ESP3 excel dataset. The excel file contains data from the 
    FlareHunter/ESP3 experiment. The data is stored in a pandas dataframe. 
    The function takes a filepath and a column identified input for the excel file
    which defines the column names in the excel file. It is also possible to define
    the UTM zone explicitly instead of loading it into the dataframe from the excel file.

    Input:
    filepath: string.
        The path to the directory where the excel file is stored.
    lon: string.
        The name of the column in the excel file that contains the longitude of the
        flare center location.
        Default: 'Average_Lon_C_Foot'
    lat: string.
        The name of the column in the excel file that contains the latitude of the
        flare center location.
        Default: 'Average_Lat_C_Foot'
    UTM_X: string.
        The name of the column in the excel file that contains the UTM x location of the
        flare center location.
        Default: 'Average_X_C_Foot'
    UTM_Y: string.
        The name of the column in the excel file that contains the UTM y location of the
        flare center location.
        Default: 'Average_Y_C_Foot'
    UTM_zone: string.
        The name of the column in the excel file that contains the UTM zone of the
        flare center location.
        Default: 'UTM_zone'
    Radius: string.
        The name of the column in the excel file that contains the radius of the
        flare footprint.
        Default: 'Average_Radius_Foot'
    Flowrate: string.
        The name of the column in the excel file that contains the flowrate of the
        flare.
        Default: 'Flow_Rate_realBRS'
    lon_user_def: int.
        The longitude of the data. If this is defined the longitude is not loaded from
        the excel file.
        Default: None
    lat_user_def: int.
        The latitude of the data. If this is defined the latitude is not loaded from
        the excel file.
        Default: None
    UTM_X_user_def: int.
        The UTM x location of the data. If this is defined the UTM x location is not loaded from
        the excel file.
        Default: None
    UTM_Y_user_def: int.
        The UTM y location of the data. If this is defined the UTM y location is not loaded from
        the excel file.
        Default: None
    UTM_zone_user_def: int.
        The UTM zone of the data. If this is defined the UTM zone is not loaded from
        the excel file.
        Default: None
    Depth_user_def: int.
        The depth of the data. If this is defined the depth is not loaded from
        the excel file.
        Default: None
    Radius_user_def: int.
        The radius of the acoustic footprint. If this is defined the radius is not loaded from
        the excel file.
        Default: None
    Flowrate_user_def: int.
        The flowrate of the data. If this is defined the flowrate is not loaded from
        the excel file.
        Default: None
    
    Output: 
    DFdata: pandas dataframe
        Containes data for all the 8 columns in row "inputrow"
    varstrings: dictionary
        Dictionary containing the column identifiers in the excel file.
    user_defs: dictionary
        Dictionary containing the user defined values.
    '''

    #Define defaults
    if lon == None and lon_user_def == None:
        lon = 'Average_Lon_C_Foot'
        warnings.warn('No longitude column defined, using default: Average_Lon_C_Foot')
    elif lon == None and lon_user_def != None:
        lon = lon_user_def
        warnings.warn('No longitude column defined, using user defined.')
    if lat == None:
        lat = 'Average_Lat_C_Foot'
        warnings.warn('No latitude column defined, using default: Average_Lat_C_Foot')
    if UTM_X == None:
        UTM_X = 'Average_X_C_Foot'
        warnings.warn('No UTM X column defined, using default: Average_X_C_Foot')
    if UTM_Y == None:
        UTM_Y = 'Average_Y_C_Foot'
        warnings.warn('No UTM Y column defined, using default: Average_Y_C_Foot')
    if UTM_zone == None and UTM_zone_user_def == None:
        UTM_zone = 'UTM_zone'
        warnings.warn('No UTM zone column defined, using default: UTM_zone')
    elif UTM_zone == None and UTM_zone_user_def != None:
        UTM_zone = UTM_zone_user_def
        warnings.warn('No UTM zone column defined, using user defined.')
    if Depth == None:
        Depth = 'Depth'
        warnings.warn('No depth column defined, using default: Depth')
    if Radius == None:
        Radius = 'Average_Radius_Foot'
        warnings.warn('No radius column defined, using default: Average_Radius_Foot')
    if Flowrate == None:
        Flowrate = 'Flow_Rate_realBRS'
        warnings.warn('No flowrate column defined, using default: Flow_Rate_realBRS')
    
    #Load the data
    DFdata = pd.read_excel(filepath,header = 0, index_col = 0, usecols = [0,1,2,3,4,5,6,7])

    varstrings = {}
    varstrings['lat'] = lon
    varstrings['lon'] = lat
    varstrings['UTM_X'] = UTM_X
    varstrings['UTM_Y'] = UTM_Y
    if UTM_zone_user_def == None:
        varstrings['UTM_zone'] = UTM_zone
    else:
        varstrings['UTM_zone'] = None
        print('UTM_zone is user defined')
    varstrings['Radius'] = Radius
    varstrings['Flowrate'] = Flowrate
    
    return DFdata,varstrings

###############################################################################################

def get_distance(x_locs,y_locs):
    '''
    Calculates the distance between the points in a vector with coordinates xlocs and ylocs. 
    The function returns a matrix with the distances between all the points in the vector.
    
    Input:
    x_locs: numpy array
        The x locations of the points.
    y_locs: numpy array
        The y locations of the points.
    
    Output:
    dist: numpy array
        A matrix with the distances between all the points in the vector.
    '''

    #Create a matrix with the distances between all the points in the vector
    dist = np.zeros((len(x_locs),len(x_locs)))

    for i in range(len(x_locs)):
        for j in range(len(x_locs)):
            dist[i,j] = np.sqrt((x_locs[i]-x_locs[j])**2+(y_locs[i]-y_locs[j])**2) 
    return dist

###############################################################################################

def get_shared_area(x_loc1,x_loc2,y_loc1,y_loc2,R1,R2):
    '''
    Calculates the shared area between two circles with radius R1 and R2 and
    to different origins located at x_loc and y_loc. The function returns the shared area.
    Reference: Weisstein, Eric W. "Circle-Circle Intersection." From MathWorld--
    A Wolfram Web Resource. http://mathworld.wolfram.com/Circle-CircleIntersection.html

    If the circles have the same origin the function returns nan.

    Input:
    x_loc1: float
        The x location of the center of circle 1.
    x_loc2: float
        The x location of the center of circle 2.
    y_loc1: float
        The y location of the center of circle 1.
    y_loc2: float
        The y location of the center of circle 2.
    R1: float
        The radius of the first circle.
    R2: float
        The radius of the second circle.

    Output:
    shared_area: float
        The shared area between the two circles in m^2.
    '''

    #Calculate the distance between the two circles
    dist = np.sqrt((x_loc1-x_loc2)**2+(y_loc1-y_loc2)**2)

    #Calculate the shared area between the two circles
    if dist < R1+R2 and dist != 0:
        #Calculate the shared area
        shared_area = R1**2*np.arccos((dist**2+R1**2-R2**2)/(2*dist*R1)) \
            +R2**2*np.arccos((dist**2+R2**2-R1**2)/(2*dist*R2))-0.5*np.sqrt((
            -dist+R1+R2)*(dist+R1-R2)*(dist-R1+R2)*(dist+R1+R2))
    else:
        shared_area = 0
    
    return shared_area

###############################################################################################

def get_area_of_footprint(depth,angle):
    '''
    Calculates the area of the footprint of the acoustic beam of the SB echosounder at
    a specified depth. The function returns the area of the footprint.

    Input:
    depth: float
        The depth to the place where you want the area of the footprint.

    angle: float
        The opening angle of the echosounder in degrees.

    Output:
    area: float
        The area of the footprint in m^2.
    '''

    #Calculate the area of the footprint
    area = np.pi*(depth*np.tan(np.deg2rad(angle/2)))**2

    return area

###############################################################################################

def get_close_flares(xloc_or_lat,
                     yloc_or_lon,
                     radius,
                     threshold = 0.2,
                     UTM_zone = 33,
                     lonlat_coord = False,
                     closeness_param = 'area'):
    
    '''
    Finds all the flares that are within a certain distance of each other or shares a certain
    amount of area. The function use UTM x an y or lan/lot coordinates and footprint radius 
    to return a list of pairs with indices of flares that are defined as close to each other 
    according to the closeness_param and threshold parameters. Can calculate closeness based 
    on distance between footprint center or the fractional (%) shared area between the footprints.

    Input:
    xloc_or_lat: numpy array
        The x locations of the flares that have at least one overlapping flare, or the latitudes
        of the flares if lonlat_coord = True.
    yloc_or_lon: numpy array
        The y locations of the flares that have at least one overlapping flare, or the longitudes
        of the flares if lonlat_coord = True.
    radius: numpy array
        The radius of the flares.
    threshold: float
        The threshold for the overlap between two flares to be clustered. If closeness_param = 'area'
        the threshold is the fractional (between 0 and 1) overlap between the flares. If closeness_param = 'distance'
        the threshold is the distance between the flares number of flare footprint radii (Veloso et al., 
        2015, doi: 10.1002/lom3.10024) used 1.8R as the threshold).
        Default: 0.2
    UTM_zone: int
        The UTM zone where the flares are located
        Default: 33
    lonlat_coord: boolean
        If True the function uses the lon/lat coordinates of the flares instead of the UTM x and y
        coordinates. Recalculates the input lon/lat coorinates to UTM x and y coordinates.

    Output:
    indices: numpy array
        A list of pairs with indices of flares that are defined as close to each other according to
        the closeness_param and threshold parameters.
    '''
    #Define indices parameter
    indices = np.array([])
    
    #check if the input coordinates are lon/lat or UTM x/y and convert to utm if 
    #lonlat_coord == True
    if lonlat_coord == True:
        [xloc_or_lat,yloc_or_lon] = utm.from_latlon(xloc_or_lat,yloc_or_lon,UTM_zone,'U')
    
    #Calculate and create a matrix with the distance between all the flares
    flare_dists = get_distance(xloc_or_lat,yloc_or_lon)

    #Get the close flares if closeness_param == 'distance'
    if closeness_param == 'distance':
        #Find the indices of the flares that are within the threshold distance of each other
        #which is given by the threshold*radius
        indices = np.transpose(np.where(flare_dists < threshold*radius))
        #check if indices is empty
        if len(indices) == 0:
            #Create error message and stop the program
            raise Exception("There are no flare observations to be clustered with the " 
                            "given closeness_param and threshold.")       
            
        #Remove all diagonal matches (where indices[i,:] is the same number)
        indices = indices[indices[:,0] != indices[:,1],:]

    #Get the close flares if closeness_param == 'area'
    if closeness_param == 'area':
        #Calculate the area of the footprint of each flare
        flare_areas = np.pi*radius**2
        #Create a matrix with the shared area between all the flares in the dataset
        flare_shared_areas = np.zeros((len(xloc_or_lat),len(xloc_or_lat)))
        for i in range(len(xloc_or_lat)):
            for j in range(len(xloc_or_lat)):
                flare_shared_areas[i,j] = get_shared_area(xloc_or_lat[i],
                xloc_or_lat[j],yloc_or_lon[i],yloc_or_lon[j],radius[i],
                radius[j])
        #Divide the flare_shared_areas with the flare_areas to get the fraction of 
        #the area that is shared between the flares
        frac_flare_shared_areas = flare_shared_areas*(1./flare_areas)
        #Find the indices of the flares that overlap with at least the overlap threshold 
        #of their area
        indices = np.transpose(np.where(frac_flare_shared_areas > threshold))
        #check if indices is empty
        if len(indices) == 0:
            raise Exception("There are no flare observations to be clustered with the  " 
                            "given closeness_param and threshold.")        
            

    #Find repeated and/or mirrored pairs in the indices array
    #Find the indices of the repeated pairs
    i = 0
    while i <= len(indices):
        if i == len(indices):
            break
        repeated_index=(np.where((indices[:,0] == indices[i,1]) & (indices[:,1] == indices[i,0])))
        i = i+1
        #Remove the repeated pairs
        indices = np.delete(indices,repeated_index,0)
    
    return indices

###############################################################################################

def create_clusters(indices):
    '''
    Creates clusters based on the indices list of clusters. Returns a list of lists with the
    indices of the flares in each cluster.

    Input:
    
    indices: numpy array
        A list of pairs with indices of flares that are defined as close to each other according to
        the closeness_param and threshold parameters.

    Output:
    
    clusterlist: list
        A list of lists containing the indices of the flares in each cluster.
        
    '''

    #create the clusterlist, i.e. a list of clusters, where each cluster is a list of indices
    clusterlist = []

    #loop over all flares
    for i in range(len(indices)):
        if i == 0:
            #add the first flare to the clusterlist
            clusterlist.append([indices[i,0],indices[i,1]])
        else:
            #loop over all clusters and check if the flare observation i should be 
            #added to any of the clusters
            foundhome = 0 #flag to check if the flare will find a cluster in the next loop
            for j in range(len(clusterlist)):
                if indices[i,0] in clusterlist[j]:
                    clusterlist[j].append(indices[i,1])
                    #keep clusterlist[j] unique
                    clusterlist[j] = list(set(clusterlist[j]))
                    foundhome = 1
                if indices[i,1] in clusterlist[j]:
                    clusterlist[j].append(indices[i,0])
                    #keep clusterlist[j] unique
                    clusterlist[j] = list(set(clusterlist[j]))
                    foundhome = 1
            #if none of the flare observations in the flare pair is not to be clustered
            #with any of the already clustered data we add it to the clusterlist as a separate
            #cluster
            if foundhome == 0:
                clusterlist.append([indices[i,0],indices[i,1]])
                #keep clusterlist[j] unique
                clusterlist[j] = list(set(clusterlist[j]))
    #Go through clusterlist and merge all clusters where one or more flare observations in the 
    #cluster are also in another cluster
    #loop over all clusters
    for i in range(len(clusterlist)):
        #loop over all clusters again
        for j in range(len(clusterlist)):
            #if cluster i and j are not the same cluster
            if i != j:
                #if any of the flare observations in cluster i are also in cluster j
                if isinstance(clusterlist[i], list) and isinstance(clusterlist[j], list):
                    if any(item in clusterlist[i] for item in clusterlist[j]):
                        #merge cluster i and j
                        clusterlist[i] = list(set(clusterlist[i]+clusterlist[j]))
                        #flag cluster j for removal
                        clusterlist[j] = 9999
    #Remove all the clusters that are flagged for removal
    clusterlist = [x for x in clusterlist if x != 9999]

    return clusterlist

###############################################################################################

def cluster_flowrate_vanilla(DFdata,UTM_X,UTM_Y,varstrings,indices):
    '''
    Clusters flares that have overlapping areas/are within a certain distance of each other
    (this is done through a different function) and calculates the total area and flowrate
    of each cluster. The function returns a dictionary with the cluster info.
    
    The method follows the method outlined in Veloso et al., 2015, doi: 10.1002/lom3.10024
    except for how two flares are judged to be close enough to be clustered together, this is done
    in a different function and used as input in this function.

    This method LinkS all flares that overlap accumulatevly, i.e. if flare 1 overlaps with flare 2
    and flare 2 overlaps with flare 3, then flare 1, 2 and 3 should be linked together.
    The flares that share area are given by the indices in the indices array.

    Input:
    DFdata: pandas dataframe
        The dataframe containing the flare data.
    UTM_X: numpy array
        The x locations of the flares that have at least one overlapping flare
    UTM_Y: numpy array
        The y locations of the flares that have at least one overlapping flare
    indices: numpy array
        Index pairs of the flares that are within threshold distance/exceed the overlap threshold 
        of each other.
    varstrings: dictionary
        Dictionary containing the column identifiers in the excel file.
    
    Output:
    clusters: dictionary
        dictionary containing the following keys:
        area: numpy array
            The total area of each cluster.
        flow: numpy array
            The total flowrate of each cluster.
        xloc: numpy array  
            The x location of the center of each cluster.
        yloc: numpy array
            The y location of the center of each cluster.
        clusterlist: list
            A list of lists containing the indices of the flares in each cluster.
        
    '''
    #Check that indices contains any indices
    if len(indices) == 0:
        warnings.warn('No clusters in indices list')
        return None

    #Create a list of lists with the indices of the flares in each cluster using the clusterlist function
    clusterlist = create_clusters(indices)

    #clusterdictionary which shall contain the cluster info we calculate
    clusters = {}

    #Calculate the total area and flowrate of each cluster
    clusters['area'] = np.zeros(len(clusterlist))
    clusters['flow'] = np.zeros(len(clusterlist))
    clusters['xloc'] = np.zeros(len(clusterlist))
    clusters['yloc'] = np.zeros(len(clusterlist))
    clusters['clusterlist'] = clusterlist
    #Create a grid with the cluster locations and areas for each cluster
    #loop over all clusters

    #Calculate the flowrate per area for each flare observation
    flow_per_area = DFdata[varstrings['Flowrate']].values/(np.pi*DFdata[varstrings['Radius']].values**2)

    for i in range(len(clusterlist)):
        #Define grid according to minimum and maximum x and y locations of the flares
        #in the cluster
        x_min = np.min(UTM_X[clusterlist[i]])-np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        x_max = np.max(UTM_X[clusterlist[i]])+np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        y_min = np.min(UTM_Y[clusterlist[i]])-np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        y_max = np.max(UTM_Y[clusterlist[i]])+np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        #Define the grid spacing
        grid_spacing = 1.0 #1m grid spacing
        #Create the grid
        x_grid = np.arange(x_min,x_max,grid_spacing)
        y_grid = np.arange(y_min,y_max,grid_spacing)
        #Extend the shortest axis of the grid to make it square
        while len(x_grid) > len(y_grid):
            y_grid = np.append(y_grid,y_grid[-1]+grid_spacing)
        while len(x_grid) < len(y_grid):
            x_grid = np.append(x_grid,x_grid[-1]+grid_spacing)
        #Create a zero matrix with the same size as the grid where we will replace 
        #the zeros with ones where the grid cell is covered by one or more flare 
        #areas
        grid = np.zeros((len(x_grid),len(y_grid)))
        #loop over all flares in the cluster
        for j in range(len(clusterlist[i])):
            #Distance between the flare and all the y coordinates in the grid
            dist_y = np.abs(y_grid-UTM_Y[clusterlist[i][j]])
            #Distance between the flare and all the x coordinates in the grid
            dist_x = np.abs(x_grid-UTM_X[clusterlist[i][j]])
            #Calculate the distance between the flare and all the grid cells
            #This will be a matrix with the same size as the grid
            dist = np.sqrt(dist_x**2+dist_y[:,None]**2)

            #Replace the zeros in the grid with ones where the grid cell is covered
            #by the flare area
            grid[np.where(dist < DFdata[varstrings['Radius']].values[clusterlist[i][j]])] = 1
        
            #Plot the grid, center, and flares in the cluster
                #Plot the overlap-map for the cluster and the flowrates for the cluster
           
        #Calculate the average flowrate per area for the cluster
        avg_flow_per_area = sum(flow_per_area[clusterlist[i]])/len(clusterlist[i])

        #sum up all the ones in the grid to get the total area covered by the flares
        clusters['area'][i] = np.sum(grid)*grid_spacing**2

        #Calculate the average flowrate of the cluster (avg_flow_per_area*area)
        clusters['flow'][i] = clusters['area'][i]*avg_flow_per_area

        #Plot the grid multiplied by the average flowrate
        plt.figure()
        plt.imshow(grid*avg_flow_per_area)
        plt.colorbar()
        plt.title('Flowrate per area of cluster '+str(i))
        plt.show()        

    ### DEPRECATED: Calculate the average flowrate of the cluster (sum of flowrates of all flares in cluster)
    #for i in range(len(clusterlist)):
    #    for j in range(len(clusterlist[i])):
    #        clusters['flow'][i] = np.mean(clusters['flow'][i] + 
    #                                      DFdata[varstrings['Flowrate']].values[clusterlist[i][j]])
    
    #************************************************************************************************

    #Calculate the geometric center of each cluster
    for i in range(len(clusterlist)):
        clusters['xloc'][i] = np.mean(UTM_X[clusterlist[i]])
        clusters['yloc'][i] = np.mean(UTM_Y[clusterlist[i]])

    return clusters

###############################################################################################

def cluster_flowrate_gridded_averaging(DFdata,UTM_X,UTM_Y,varstrings,indices):
    '''
    Clusters flares that have overlapping areas/are within a certain distance of each other
    (this is done through a different function) and calculates the total area and flowrate
    of each cluster. The function returns a dictionary with the cluster info.
    
    The method follows the method outlined in the memo accompanying this repository. Essensially
    the method defines a grid for the cluster area, finds the gridded flux per unit area for 
    each flare observation and calculates the average where flare observation areas overlap.
    Sums up the results for each cluster.

    The first part of this script is the same as the cluster_flowrate_vanilla function, since 
    it essentially only defines the structure of the output dictionary and defines a
    grid. 

    Input:
    DFdata: pandas dataframe
        The dataframe containing the flare data.
    UTM_X: numpy array
        The x locations of the flares that have at least one overlapping flare
    UTM_Y: numpy array
        The y locations of the flares that have at least one overlapping flare
    indices: numpy array
        The indices of the flares that have at least one overlapping flare
    varstrings: dictionary
        Dictionary containing the column identifiers in the excel file.
    
    Output:
    clusters: dictionary
        dictionary containing the following keys:
        area: numpy array
            The total area of each cluster.
        flow: numpy array
            The total flowrate of each cluster.
        xloc: numpy array  
            The x location of the center of each cluster.
        yloc: numpy array
            The y location of the center of each cluster.
        clusterlist: list
            A list of lists containing the indices of the flares in each cluster.
    '''

     #Check that indices contains any indices
    if len(indices) == 0:
        warnings.warn('No clusters in indices list')
        return None

    #Create a list of lists with the indices of the flares in each cluster using the clusterlist function
    clusterlist = create_clusters(indices)

    #clusterdictionary which shall contain the cluster info we calculate
    clusters = {}

    #Calculate the total area and flowrate of each cluster
    clusters['area'] = np.zeros(len(clusterlist))
    clusters['flow'] = np.zeros(len(clusterlist))
    clusters['xloc'] = np.zeros(len(clusterlist))
    clusters['yloc'] = np.zeros(len(clusterlist))
    clusters['clusterlist'] = clusterlist

    #loop over all clusters and define a grid and 
    for i in range(len(clusterlist)):
        #Define grid according to minimum and maximum x and y locations of the flares
        #in the cluster
        x_min = np.min(UTM_X[clusterlist[i]])-np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        x_max = np.max(UTM_X[clusterlist[i]])+np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        y_min = np.min(UTM_Y[clusterlist[i]])-np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        y_max = np.max(UTM_Y[clusterlist[i]])+np.max(DFdata[varstrings['Radius']].values[clusterlist[i]])
        #Define the grid spacing
        grid_spacing = 1.0 #1m grid spacing
        #Create the grid
        x_grid = np.arange(x_min,x_max,grid_spacing)
        y_grid = np.arange(y_min,y_max,grid_spacing)
        #Extend the shortest axis of the grid to make it square (easier to work with)
        while len(x_grid) > len(y_grid):
            y_grid = np.append(y_grid,y_grid[-1]+grid_spacing)
        while len(x_grid) < len(y_grid):
            x_grid = np.append(x_grid,x_grid[-1]+grid_spacing)
        #Create two zero matrices with the same size as the grid, one to collect the flowrates and 
        #one to collect the areas and overlapping areas (represented by ones, twos, threes, etc.)
        grid_flow = np.zeros((len(x_grid),len(y_grid)))
        grid_overlap = np.zeros((len(x_grid),len(y_grid)))
        #loop over all flares in the cluster and calculate the flux per unit area for each flare observation
        #and take the average where flare observation areas overlap
        for j in range(len(clusterlist[i])):
            #Distance between the flare and all the y coordinates in the grid
            dist_y = np.abs(y_grid-UTM_Y[clusterlist[i][j]])
            #Distance between the flare and all the x coordinates in the grid
            dist_x = np.abs(x_grid-UTM_X[clusterlist[i][j]])
            #Calculate the distance between the flare and all the grid cells
            #This will be a matrix with the same size as the grid
            dist = np.sqrt(dist_x**2+dist_y[:,None]**2)
            #collect the indices for all the grid cells that are covered by the flare
            indices = np.where(dist < DFdata[varstrings['Radius']].values[clusterlist[i][j]])
            #calculate the area of the gridded flare area
            area = len(indices[0])*grid_spacing**2
            #calculate the flux per unit area for the flare
            flux_per_area = DFdata[varstrings['Flowrate']].values[clusterlist[i][j]]/area
            #add the flux per unit area to the grid_flow matrix
            grid_flow[indices] = grid_flow[indices] + flux_per_area
            #add ones to the grid_overlap matrix where the flare is located
            grid_overlap[indices] = grid_overlap[indices] + 1
        
        #Divide elementwise with grid_overlap to get the average flux per unit area for each grid cell
        #where grid_overlap is not zero
        grid_flow[np.where(grid_overlap != 0)] = grid_flow[np.where(grid_overlap != 0)]/grid_overlap[np.where(grid_overlap != 0)]

        #Plot the overlap-map for the cluster and the flowrates for the cluster
        plt.figure()
        plt.subplot(1,2,1)
        #Plot the grid_overlap matrix in a colorplot with discrete colors using something like pcolor
        im = plt.imshow(grid_overlap)
        cb = plt.colorbar(im,fraction=0.046, pad=0.04)
        #Make colorbar ticks integers
        cb.set_ticks(np.arange(0,np.max(grid_overlap)+1,1))
        #Change the size of the colorbar
        #Set limits for colorbar
        plt.title('Number of observations')
        #Increase the horizontal distance between the plots
        plt.subplots_adjust(wspace=0.5)
        plt.subplot(1,2,2)
        im2 = plt.imshow(grid_flow)
        #Add a colorbar to the right of the subfigure
        cb = plt.colorbar(im2,fraction=0.046, pad=0.04)


        
        #Position the colorbar on the right hand side of the plot
        plt.title('Average flux per unit area')
        plt.show()

        #Calculate the total area of the cluster, this is just the number of elements in the grid_overlap
        #matrix that are not zero times the grid_spacing squared
        clusters['area'][i] = np.sum(grid_overlap != 0)*grid_spacing**2
        #Calculate the total flux of the cluster by dividing grid_flow elementwise with grid_overlap where
        #grid_overlap is not zero and summing up the resuls
        clusters['flow'][i] = np.sum(grid_flow)

        #Calculate the geometric center of each cluster
        for i in range(len(clusterlist)):
            clusters['xloc'][i] = np.mean(UTM_X[clusterlist[i]])
            clusters['yloc'][i] = np.mean(UTM_Y[clusterlist[i]])

        

    return clusters

###############################################################################################

def save_clustered_data(filepath,clusters,indices,DFdata,varstrings):
    '''
    Creates a dataframe with clustered flares and their locations and flowrates together with 
    the flares that were not clustered as individual clusters. Saves the dataframe to an excel file
    with path/filename filepath.

    Input:
    filepath: string
        Path and filename of the excel file to be stored.
    clusters: dictionary
        Dictionary containing the following keys:
        area: numpy array
            The total area of each cluster.
        flow: numpy array
            The total flowrate of each cluster.
        xloc: numpy array  
            The x location of the center of each cluster.
        yloc: numpy array
            The y location of the center of each cluster.
        clusterlist: list
            A list of lists containing the indices of the flares in each cluster.
    indices: numpy array
        The indices of the flares that have at least one overlapping flare
    DFdata: pandas dataframe
        The dataframe containing the unclustered flare data.
    varstrings: dictionary
        Dictionary containing the column identifiers in the excel file.
    
    Output:
    DFclustered: pandas dataframe
        Dataframe containing the clustered flare data.
    '''
    
    #create a new dataframe with the same columns as DFdata, but replace the 
    #index column name with 'cluster_id'

    DFclustered = pd.DataFrame(columns = DFdata.columns)

    #Remove the radius column and the Flow_Rate_realBRS column
    DFclustered.drop(varstrings['Radius'],axis=1,inplace=True)
    DFclustered.drop(varstrings['Flowrate'],axis=1,inplace=True)

    #Get the UTM_Zone information into a number
    UTM_Zone = DFdata[varstrings['UTM_zone']][0]
    UTM_Zone = ''.join(filter(str.isdigit, UTM_Zone))
    UTM_Zone = int(UTM_Zone)
    #calculate the lon and lat of the clusters using the UTM coordinates and the utm package
    lonlat = utm.to_latlon(clusters['xloc'],clusters['yloc'],UTM_Zone,'U')
        
    #Calculate the average area of all the flare observations
    avg_area = (np.pi*DFdata[varstrings['Radius']].values**2)

    #Define opening angle of the echosounder to be able to calculate the depth column
    opening_angle_ES = 6.81 #degrees

    ### Add all the clustered and non-clustered data to the DFclustered dataframe ###
    #Add clustered data:

    # Create a list to hold all the cluster data
    data = []

    for i in range(len(clusters['area'])):
        #Create a dictionary with the cluster data for index i
        new_data = {
        'cluster_id': 'cluster_' + str(i+1),
        varstrings['UTM_X']: clusters['xloc'][i],
        varstrings['UTM_Y']: clusters['yloc'][i],
        varstrings['lat']: lonlat[1][i],
        varstrings['lon']: lonlat[0][i],
        'UTM_zone': DFdata[varstrings['UTM_zone']][i],
        'Area [m^2]': clusters['area'][i],
        'Average_depth': -np.mean(np.sqrt(avg_area[clusters['clusterlist'][i]])/
                                 np.sqrt(np.pi*np.tan(np.deg2rad(opening_angle_ES/2))**2)),
        'Total_Flowrate': clusters['flow'][i],
        'Flares in cluster': len(clusters['clusterlist'][i])}
        #Append the dictionary to the data list
        data.append(new_data)

    # Create a DataFrame from all the dictionaries in the data list and concatanate them
    # into one DFclustered dataframe
    # Create a DataFrame from all the dictionaries in the data list
    DFclustered = pd.DataFrame(data)

    #Add all the non-clustered data: 

    all_indices = np.arange(len(DFdata[varstrings['Radius']]))
    # Find indices that are not part of the indices array
    indices_lonely = np.setdiff1d(all_indices, indices[:, 0])
    indices_lonely = np.setdiff1d(indices_lonely, indices[:, 1])

    # Create a list to hold all the lonely indices data
    lonely_data = []

    # Add lonely indices data to the list
    for i in range(len(indices_lonely)):
        new_data = {
            'cluster_id': 'cluster_' + str(i+1+len(clusters['area'])),
            varstrings['UTM_X']: DFdata[varstrings['UTM_X']].values[indices_lonely[i]],
            varstrings['UTM_Y']: DFdata[varstrings['UTM_Y']].values[indices_lonely[i]],
            varstrings['lat']: DFdata[varstrings['lat']].values[indices_lonely[i]],
            varstrings['lon']: DFdata[varstrings['lon']].values[indices_lonely[i]],
            'UTM_zone': DFdata[varstrings['UTM_zone']][indices_lonely[i]],
            'Area [m^2]': np.round(np.pi * DFdata[varstrings['Radius']].values[indices_lonely[i]]**2, 0),
            'Average_depth': -DFdata[varstrings['Radius']].values[indices_lonely[i]] / np.tan(np.deg2rad(opening_angle_ES / 2)),
            'Total_Flowrate': DFdata[varstrings['Flowrate']].values[indices_lonely[i]],
            'Flares in cluster': 1
        }
        DFclustered = pd.concat([DFclustered, pd.DataFrame(new_data, index=[0])], ignore_index=True)

    # Create a DataFrame from the lonely indices data list
    #DFclustered = pd.concat([pd.DataFrame(d, index=[len(clusters['area'])]) for d in lonely_data], ignore_index=True)
    DFclustered.set_index('cluster_id', inplace=True)
    #Save the dataframe to a xlsx file
    DFclustered.to_excel(filepath)

    return DFclustered

###############################################################################################

def write_cluster_textfile(filepath,clusterlist,indices,DFdata):
    '''
    Writes a textfile showing which flares are in which cluster and the cluster name as well 
    as the names of the flares that have not been clustered

    Input:
    filepath: string
        Path to the location where the textfile is to be stored.
    clusterslist: list
        A list of lists containing the indices of the flares in each cluster.
    indices: numpy array
        The indices of the flares that have at least one overlapping flare
    DFdata: pandas dataframe
        The dataframe containing the unclustered flare data.
    
    Output:
    None (writes a textfile to the filepath location)

    '''
    with open(filepath.rstrip('.xlsx')+'clusterlist.txt','w') as f:
        #Star with a list of hashtags
        f.write('########################################\n')
        #make a headline saying that this is the clustered flare list
        f.write('##### Clustered flare observations #####\n')
        f.write('########################################\n')
        f.write('\n')
        for i in range(len(clusterlist)):
            f.write('cluster_' + str(i+1))
            #List all the flare names in the clusterb ("Field_Name" in the input file)
            for j in range(len(clusterlist[i])):
                if j == 0:
                    f.write('\t' + DFdata.index[clusterlist[i][j]] + '\n')
                else:
                    f.write('\t\t' + DFdata.index[clusterlist[i][j]] + '\n')
            f.write('\n')
            f.write('\n')
        #make a list of hastags to separate the clustered flares from the non-clustered flares
        f.write('##########################################\n')
        f.write('#### Non-clustered flare observations ####\n')
        f.write('##########################################\n')
        f.write('\n')
        #List all the flare names that were not clustered
        counter = 0
        for i in range(len(DFdata.index)):
            if i not in indices[:,0] and i not in indices[:,1]:
                f.write('cluster_' + str(counter+len(clusterlist)+1))
                f.write('\t' + DFdata.index[i] + '\n')
                counter = counter + 1
        #Save the file to the same folder as the input file

###############################################################################################

def master_func(filepath,
                closeness_param,
                threshold,
                method = 'gridded_averaging',
                plot = True):
    '''
    Function that do the clustering using the functions described above. Returns a dataframe with
    the clustered flare data and saves the dataframe to a new excel file. Also makes a plot of all the
    flares and the clusters if plot parameter plot = True.

    Input:
    filepath: string
        Path and filename of the excel file to be stored.
    closeness_param: string
        The preferred method for clustering the flares. Options are 'distance' and 'area'.
    threshold: float
        The threshold for the overlap between two flares to be clustered. If closeness_param = 'area'
        the threshold is the fractional (between 0 and 1) overlap between the flares. If closeness_param = 'distance'
        the threshold is the distance between the flare observation centerpoints in averaged acoustic footprint radii 
        of the two observations (Veloso et al., 2015, doi: 10.1002/lom3.10024) used 1.8R as the threshold).
    method: string
        The method used to calculate the flowrate of the clusters. Options are 'vanilla' and 'gridded_averaging'.
        Default: 'gridded_averaging'
    plot: boolean
        If True the function makes a plot of all the flares and the clusters.
        Default: True
    
    Output:
    DFclustered: pandas dataframe
        Dataframe containing the clustered flare data.

    Creates an .xslx file with the clustered flare data named "filename + clustered.xlsx" and 
    stores it in the same folder as filename. Creates a plot if plot=True. Creates a .txt file
    with the names of the flares in each cluster and the cluster name and the names of the flares
    that were not clustered.
    '''
    ### Load the data ###
    DFdata,varstrings = load_flare_data(filepath)

    ### clustering ###
    #Find flares that are close enough/have enough overlapping area to be clustered
    indices = get_close_flares(DFdata[varstrings['UTM_X']].values, 
                     DFdata[varstrings['UTM_Y']].values, 
                     DFdata[varstrings['Radius']].values, 
                     threshold = threshold,
                     UTM_zone = float(DFdata[varstrings['UTM_zone']][0][0:1]), #Getting utm-zone from data
                     lonlat_coord = False,
                     closeness_param = closeness_param)

    #Calculate the area, center location and flowrate of the clusters

    #Check if the user wants to use the gridded averaging method or the vanilla method
    if method == 'vanilla':
        clusters = cluster_flowrate_vanilla(DFdata,
                                    DFdata[varstrings['UTM_X']].values,
                                    DFdata[varstrings['UTM_Y']].values,
                                    varstrings,
                                    indices)
    elif method == 'gridded_averaging':
        clusters = cluster_flowrate_gridded_averaging(DFdata,
                                    DFdata[varstrings['UTM_X']].values,
                                    DFdata[varstrings['UTM_Y']].values,
                                    varstrings,
                                    indices)
    else:
        warnings.warn('Method not recognized, using gridded averaging method')
        clusters = cluster_flowrate_gridded_averaging(DFdata,
                                    DFdata[varstrings['UTM_X']].values,
                                    DFdata[varstrings['UTM_Y']].values,
                                    varstrings,
                                    indices)
    
    ### Saving and plotting ### 
    #Save the clustered data and non-clustered data to a new excel file
    DFclustered = save_clustered_data(filepath.rstrip('.xlsx')+'clustered.xlsx',
                        clusters,
                        indices,
                        DFdata,
                        varstrings)
    
    #Make and save a textfile containing a list of all the flares that have been clustered
    #and the cluster they belong to.
    write_cluster_textfile(filepath,clusters['clusterlist'],indices,DFdata)

    #Create a textfile with the names of the flares in each cluster and the cluster name
    #and all the flares that were not clustered    

    if plot == True:
        #Make a plot of all the clustered and non-clustered flare areas on a map
        #Import map of the area

        
        plt.figure()
        plt.scatter(DFdata[varstrings['UTM_X']].values,DFdata[varstrings['UTM_Y']].values,
                    s = 2*np.pi*DFdata[varstrings['Radius']].values,
                    c = DFdata[varstrings['Flowrate']].values)
        plt.scatter(clusters['xloc'],clusters['yloc'],s = clusters['area'],
                    c = clusters['flow'],marker = 'x')
        plt.xlabel('UTM X [m]')
        plt.ylabel('UTM Y [m]') 
        #plt.title('Acoustic footprints and clustered flares')
        #Write a textbox explaining that the size of the circles are the footprint areas
        #color is the flowrate and the x's are where the clusters are located
        textstr = '\n'.join((
            r'Circle size: Flare footprint area',
            r'Color: Flare flowrate',
            r'X: Cluster center'))
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.2)
        plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        
        plt.colorbar()
        plt.show()
    
    return DFclustered

###############################################################################################

def run_clustering():
    filepath = entry_filepath.get().replace('\\', '\\\\')
    #Check that filepath does not contain double double backslashes
    filepath.replace('\\\\\\\\','\\\\')
    closeness_param = entry_closeness_param.get()
    threshold = float(entry_threshold.get())
    method = entry_method.get()
    
    # Call your master_func with the retrieved input values
    master_func(filepath, closeness_param, threshold, method = method, plot=True)

'''
GUI function
'''

###############################################################################################
#---------------------------------------------------------------------------------------------#
###############################################################################################

################################################
################# INITIATION ###################
################################################

if __name__ == '__main__':

    #Run GUI version or non gui version trigger

    runGUI = True #Set to True to run the GUI version, False to run the non GUI version

    if runGUI == True:

        #######################################################
        ################# NON GUI VERSION #####################
        #######################################################
        
        ### Set input parameters ###
        #Path to the excel file containing the flare data
        #PS: Don't use double backslashes, don't remove the r.
        filepath = r'filepath\filename.xlsx'
                
        #Preferred method for clustering the flares. Options are 'distance' and 'area'
        closeness_param = 'distance' #can be 'area' or 'distance'

        #Threshold for clustering the flares. If closeness_param = 'distance' the threshold 
        # is the distance between the flares in number of flare footprint radii 
        #(Veloso et al., 2015, doi: 10.1002/lom3.10024) used 1.8R as the threshold). If 
        #closeness_param = 'area' the threshold is the fractional (between 0 and 1) overlap 
        # between the flares. 
        threshold = 1.99 #can be fraction of overlapping area, or number of flare footprint radii

        #Run master function
        master_func(filepath,
                    closeness_param,
                    threshold,
                    method = 'vanilla',
                    plot=True)

    ##################################################
    ################# GUI VERSION ####################
    ##################################################

    if runGUI == True:

        #Create a GUI to select the input parameters and run the clustering algorithm on the data 
        #and save the clustered data to a new excel file
        #Function to execute when the "Run" button is clicked

        # Create a GUI
        root = tk.Tk()
        root.title('Flare clustering')
        root.geometry('500x500')

        # Create a frame for the input parameters
        frame_input = tk.Frame(root)
        frame_input.pack(side='top', fill='both', expand=True)

        # Create a frame for the buttons
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(side='bottom', fill='both', expand=True)

        # Add a field for the filepath
        label_filepath = tk.Label(frame_input, text='File location and path:')
        label_filepath.grid(row=0, column=0)
        entry_filepath = tk.Entry(frame_input)
        entry_filepath.grid(row=0, column=1)
        #Make this field larger
        entry_filepath.config(width=50)

        # Add a field for the closeness parameter
        label_closeness_param = tk.Label(frame_input, text='Closeness parameter:')
        label_closeness_param.grid(row=1, column=0)
        #make entry with default value
        entry_closeness_param = tk.Entry(frame_input)
        entry_closeness_param.insert(0, 'distance')
        entry_closeness_param.grid(row=1, column=1)

        # Add a field for the thresholds
        label_threshold = tk.Label(frame_input, text='Threshold:')
        label_threshold.grid(row=2, column=0)
        entry_threshold = tk.Entry(frame_input)
        #Create a default value
        entry_threshold.insert(0, '1.99')
        entry_threshold.grid(row=2, column=1)

        # Add a field for the method
        label_method = tk.Label(frame_input, text='Method:')
        label_method.grid(row=3, column=0)
        entry_method = tk.Entry(frame_input)
        #Create a default value
        entry_method.insert(0, 'gridded_average')
        entry_method.grid(row=3, column=1)

        # Add a button to run the clustering algorithm
        button_run = tk.Button(frame_buttons, text='Run', command=run_clustering)
        button_run.pack(side='left', fill='both', expand=True)

        # Start the GUI main event loop
        root.mainloop()

        #Add a square in the gui where a plot of the clusterd as well as non-clustered flares 
        #is shown
        '''
        #Make a square for the plot in the gui
        plt.figure()
        plt.scatter(DFdata[varstrings['UTM_X']].values,DFdata[varstrings['UTM_Y']].values,
                    s = 2*np.pi*DFdata[varstrings['Radius']].values,
                    c = DFdata[varstrings['Flowrate']].values)
        plt.scatter(clusters['xloc'],clusters['yloc'],s = clusters['area'],
                    c = clusters['flow'],marker = 'x')
        plt.xlabel('UTM X [m]')
        plt.ylabel('UTM Y [m]')
        plt.title('Acoustic footprints and clustered flares')
        #Write a textbox explaining that the size of the circles are the footprint areas
        #color is the flowrate and the x's are where the clusters are located
        textstr = '\n'.join((
            r'Circle size: Flare footprint area',
            r'Color: Flare flowrate',
            r'X: Cluster center'))
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.2)
        plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        #Make the plot appear in the gui
        
        canvas = FigureCanvasTkAgg(plt.gcf(), master=root)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        #Add a toolbar to the plot
        toolbar = NavigationToolbar2Tk(canvas, root)
        toolbar.update()
        '''
    
    
