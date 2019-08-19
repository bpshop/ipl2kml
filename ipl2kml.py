import numpy as np
import simplekml
import sys
sys.path.insert(0, './../geolib')
import swiss_projection


# my_int equals int but returns 0 in case of an empty string
# or an string with only blanks
def my_int(my_string):
    my_string.replace(' ', '')
    if len(my_string) == 0:
        return 0
    if len(my_string) == 1:
        if ord(my_string) == 32:
            return 0
    nb_spaces = 0
    for car in my_string:
        if ord(car) == 32:
            nb_spaces = nb_spaces + 1
    if nb_spaces == len(my_string):
        return 0
    return int(float(my_string))

######################
# #### READ IPL ######
######################

# ## Parameters
# dash length and dash spaces
dash_space = 20
# part of the line with dashes
dash_part = 0.25

# ## read file

#####################################
# ###### HIER ANPASSEN ##############
#####################################
fname = "rempen14_frei.IPL"


# fname root
fname_root = fname.split(".")


lines = [line.rstrip('\n') for line in open(fname)]
# with open(fname) as f:
#     lines = f.readlines()

title1 = lines[0]
title2 = lines[1]
net_type = lines[2][0:8]

if net_type != "LAGENETZ":
    print("Program does only work with LAGENETZ")
    temp = raw_input("Press ENTER to end...")
    sys.exit()

i = 7

point_name_per_index = {}
point_index_per_number = {}
point_coordinates = []

# ## PUNKTE
nb_pt = 0
while True:
    # end of the point section
    if lines[i].strip() == "MESSUNGEN":
        break
    
    # read point type
    point_name = lines[i][1:17]
    point_name = point_name.strip()
    point_numb = int(lines[i][19:27])
    point_east = float(lines[i][27:41])
    point_north = float(lines[i][41:55])
    
    i = i + 1

    if point_name == "PLOT":
        continue
    
    point_name_per_index[nb_pt] = point_name
    point_index_per_number[point_numb] = nb_pt
    temp = [nb_pt, point_east, point_north]
    point_coordinates.append(temp)
    nb_pt = nb_pt + 1

i = i + 1
observations = []
# ## MESSUNGEN
while True:
    # end of the point section
    if lines[i].strip() == "VERSCHIEBUNGEN":
        break
    
    pt1 = my_int(lines[i][2:10])
    pt2 = my_int(lines[i][10:18])
    gnss = my_int(lines[i][33:34])
    dist = my_int(lines[i][39:40])
    hz = my_int(lines[i][46:48])
    v = my_int(lines[i][78:80])

    index1 = point_index_per_number[pt1]
    index2 = point_index_per_number[pt2]
    temp = [index1, index2, gnss, dist, hz, v]
    observations.append(temp)    
    i = i+1

i = i + 1
displacements = []
# ## VERSCHIEBUNGEN
while True:
    # end of the point section
    if lines[i].strip() == "ELLIPSEN":
        break
    
    pt1 = my_int(lines[i][2:10])
    x = float(lines[i][10:20])
    y = float(lines[i][20:30])
    index1 = point_index_per_number[pt1]
    temp = [index1, x, y]
    displacements.append(temp)
    i = i+1

i = i + 1
ellipses = []
# ## ELLIPSEN
while True:
    # end of the point section
    if lines[i].strip() == "ZUVERLAESSIGKEIT":
        break
    
    pt1 = my_int(lines[i][2:10])
    x = float(lines[i][10:20])
    y = float(lines[i][20:30])
    az = float(lines[i][20:30])
    index1 = point_index_per_number[pt1]
    temp = [index1, x, y, az]
    ellipses.append(temp)
    i = i+1

i = i + 1
robustness = []
# ## ZUVERLAESSIGKEIT
while True:
    # end of the point section
    if lines[i].strip() == "ENDE":
        break
    
    pt1 = my_int(lines[i][2:10])
    x = float(lines[i][10:20])
    y = float(lines[i][20:30])
    az = float(lines[i][30:40])
    index1 = point_index_per_number[pt1]
    temp = [index1, x, y, az]
    robustness.append(temp)
    i = i+1

# ## Identify reverse measurements
# ##    0 ind1
# ##    1 ind2
# ##    2 gnss
# ##    3 dist1
# ##    4 hz1
# ##    5 v1
# ##    6 dist2
# ##    7 hz2
# ##    8 v2

observations2 = []
for meas in observations:
    ind1 = meas[0]
    ind2 = meas[1]

    inv = 0
    if ind2 > ind1:
        temp = ind1
        ind1 = ind2
        ind2 = temp
        inv = 1

    found = 0
    for i in range(0, len(observations2)):
        if observations2[i][0] == ind1 and observations2[i][1] == ind2:
            found = 1
            observations2[i][2] = observations2[i][2] + meas[2]  # gnss
            if inv == 0:
                my_off = 0
            if inv == 1:
                my_off = 3
            observations2[i][3 + my_off] = observations2[i][3 + my_off] + meas[3]  # dist
            observations2[i][4 + my_off] = observations2[i][4 + my_off] + meas[4]  # hz
            observations2[i][5 + my_off] = observations2[i][5 + my_off] + meas[5]  # v
            break

    if found == 0:
        if inv == 0:
            temp = [ind1, ind2, meas[2], meas[3], meas[4], meas[5], 0, 0, 0]
        if inv == 1:
            temp = [ind1, ind2, 0, 0, 0, meas[2], meas[3], meas[4], meas[5]]
        observations2.append(temp)

#######################
# #### WRITE KML ######
#######################

# Add points
kml = simplekml.Kml()

help_pts = 0
for pt_coo in point_coordinates:
    pt_index = pt_coo[0]
    Y = pt_coo[1]
    X = pt_coo[2]

    if not (2000000 < Y < 3000000):
        print("Program does only work with LV95 till now (Y)")
        temp = raw_input("Press ENTER to end...")
        sys.exit()

    if not (1000000 < X < 2000000):
        print("Program does only work with LV95 till now (X)")
        temp = raw_input("Press ENTER to end...")
        sys.exit()

    if len(point_name_per_index[pt_index]) == 0:
        help_pts = help_pts + 1
        continue
    
    llh = swiss_projection.lv95_to_wgs84([Y, X, 800])
    pnt = kml.newpoint(name=point_name_per_index[pt_index],
                       coords=[(llh[0], llh[1])])  # lon, lat optional height
print(str(help_pts) + " point(s) ignored (intermediate points)")


# Add measurements
for meas in observations2:
    ind1 = meas[0]
    ind2 = meas[1]

    gnss = meas[2]

    dist = [meas[3], meas[6]]
    hz = [meas[4], meas[7]]
    v = [meas[5], meas[8]]

    Y1 = point_coordinates[ind1][1]
    X1 = point_coordinates[ind1][2]
    Y2 = point_coordinates[ind2][1]
    X2 = point_coordinates[ind2][2]

    Y3 = 0.5*Y1 + 0.5*Y2
    X3 = 0.5*X1 + 0.5*X2

    dY = Y2 - Y1
    dX = X2 - X1

    Y4 = 0.4*dY + Y1
    X4 = 0.4*dX + X1

    Y5 = 0.6*dY + Y1
    X5 = 0.6*dX + X1

    llh1 = swiss_projection.lv95_to_wgs84([Y1, X1, 800])
    llh2 = swiss_projection.lv95_to_wgs84([Y2, X2, 800])
    llh3 = swiss_projection.lv95_to_wgs84([Y3, X3, 800])
    
    check = [0, 0]
    case = [0, 0]

    if gnss > 0:
        pnt = kml.newpoint(name=point_name_per_index[pt_index],
                           coords=[(llh1[0], llh1[1])])  # lon, lat optional height
        pnt.style.iconstyle.icon.href = 'https://api3.geo.admin.ch/color/255,0,0/star-24@2x.png'
        pnt = kml.newpoint(name=point_name_per_index[pt_index],
                           coords=[(llh2[0], llh2[1])])  # lon, lat optional height
        pnt.style.iconstyle.icon.href = 'https://api3.geo.admin.ch/color/255,0,0/star-24@2x.png'

    angle = [0, 0]
    angle[0] = hz[0]+v[0]
    angle[1] = hz[1]+v[1]

    # if no angle is there, only draw the distance
    if angle[0] == 0 and angle[1] == 0:
        # draw distance if indicated
        if dist[0] > 0 or dist[1] > 0:
            llh4 = swiss_projection.lv95_to_wgs84([Y4, X4, 800])
            llh5 = swiss_projection.lv95_to_wgs84([Y5, X5, 800])
            line3 = kml.newlinestring(name="test", coords=[(llh4[0], llh4[1]), (llh5[0], llh5[1])])
            line3.style.linestyle.color = 'ff0000ff'  # red
            line3.style.linestyle.width = 6  # 2 pixels
        continue

    # draw both lines
    line1 = kml.newlinestring(name="test", coords=[(llh1[0], llh1[1]), (llh3[0], llh3[1])])
    line2 = kml.newlinestring(name="test", coords=[(llh3[0], llh3[1]), (llh2[0], llh2[1])])

    # color of line 1
    if angle[0] > 0:
        line1.style.linestyle.color = 'ff0000ff'  # red
        line1.style.linestyle.width = 2  # 2 pixels
    else:
        line1.style.linestyle.color = '64F00014'  # blue
        line1.style.linestyle.width = 2  # 2 pixels

    # color of line 2
    if angle[1] > 0:
        line2.style.linestyle.color = 'ff0000ff'  # red
        line2.style.linestyle.width = 2  # 2 pixels
    else:
        line2.style.linestyle.color = '64F00014'  # blue
        line2.style.linestyle.width = 2  # 2 pixels

    # draw distance
    if dist[0] > 0 or dist[1] > 0:
        llh4 = swiss_projection.lv95_to_wgs84([Y4, X4, 800])
        llh5 = swiss_projection.lv95_to_wgs84([Y5, X5, 800])
        line3 = kml.newlinestring(name="test", coords=[(llh4[0], llh4[1]), (llh5[0], llh5[1])])
        line3.style.linestyle.color = 'ff0000ff'  # red
        line3.style.linestyle.width = 6  # 2 pixels
        
kml.save(fname_root[0] + ".kml")

print("program run successful")
temp = raw_input("Press ENTER to end...")
