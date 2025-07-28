# %%
import s3fs
import zarr
from cartopy import crs, feature
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import colormaps
import datetime
import os
import imageio.v2 as imageio
import contextily as cx

# %%
# Date and simulation length
start_date = datetime.datetime.strptime("20250522_00","%Y%m%d_%H")
simulation_length = 24 * 16 # 24 hours for 7 days
# simulation_length = 1 * 1

# Image folder path
image_folder ='contents/maps/real'

# Colormap
cmap = colors.ListedColormap([(0,0,0,0),'yellowgreen','gold','orange','red','firebrick','orchid','purple'])
bounds =[0, 50, 100, 150, 200, 250, 300, 10000]
norm =colors.BoundaryNorm(bounds, cmap.N)

# Setup s3 connection
url = "s3://hrrrzarr"
fs = s3fs.S3FileSystem(anon=True)

# Open the connection and read the index file
store = zarr.open(s3fs.S3Map(url, s3=fs))
index = store["grid/HRRR_chunk_index.zarr"]

# Bounds
min_lat= 41
max_lat = 58
min_long = -110
max_long = -80

# %%
for time_delta in range(simulation_length):

    analysis_time = start_date + datetime.timedelta(hours=time_delta)
    string_date = analysis_time.strftime('%Y%m%d')
    string_hour = analysis_time.strftime('%H')
    path = f"sfc/{string_date}/{string_date}_{string_hour}z_anl.zarr/8m_above_ground/MASSDEN/8m_above_ground/MASSDEN"

    try:
        smoke = store[path]
        pass
    except KeyError:
        continue
        
    # Instantiate plot
    fig, ax = plt.subplots(subplot_kw={'projection':crs.Mercator()})
    ax.set_extent([min_long,max_long,min_lat,max_lat], crs=crs.PlateCarree())
    ax.contourf(index["longitude"], index["latitude"], smoke[:]*1e9,levels=bounds,cmap=cmap,norm=norm, transform=crs.PlateCarree())
    cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, attribution_size=5)

    # Add date and time text
    plt.text(x = 0.72, y = 0.90, transform=ax.transAxes,
             s=f'{analysis_time.strftime("%d %b, %Y")}\n{analysis_time.strftime("%H:%M")}',
             fontdict = {
                'family': 'sans-serif',
                'color':  'white',
                'weight': 'normal',
                'size': 12,
                'multialignment': 'right'
             }
    )
    
    # Add title
    plt.text(x = 0.01, y = 0.90, transform=ax.transAxes,
            s='Nopiming Provincial\nPark wildfire',
            fontdict = {
            'family': 'sans-serif',
            'color':  'white',
            'font': 'normal',
            'size': 12,
            'multialignment': 'left'
            }
    )
    
    # Add country borders
    country_borders = feature.NaturalEarthFeature(
        category='cultural',
        name='admin_0_boundary_lines_land',
        scale='50m',
        facecolor='none')
    ax.add_feature(country_borders, edgecolor='gray', alpha=0.5, linewidth=1)

    # Save it
    plt.savefig(os.path.join(image_folder,f'smoke_{string_date}_{string_hour}.png'), dpi=300, bbox_inches='tight')
    plt.show()
    plt.close(fig)
    print(f"Saved smoke_{string_date}_{string_hour}.png")



# %%
# Get a sorted list of all png files in the folder
image_files =sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith('.png')])

# Read the smoke maps using imageio
images =[imageio.imread(image_file) for image_file in image_files]

# Create an animated GIF from smoke maps
# imageio.mimwrite('Animation_5.gif', images, duration=10)

writer = imageio.get_writer('NopimingSmokeTimelapse.mp4', fps=10)

for im in image_files:
    writer.append_data(imageio.imread(im))
writer.close()

print(f"Animation saved!")


