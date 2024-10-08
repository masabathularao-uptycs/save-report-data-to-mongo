import matplotlib
# import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
import io
from collections import defaultdict
from PIL import Image, ImageOps, ImageDraw
matplotlib.use('Agg')
plt = matplotlib.pyplot

# sns.set_theme(palette="dark", font="arial")
outer_background_color="#191b1f"
text_color="#FDFEFE"
sns.set(rc={"text.color": text_color})

FIGURE_WIDTH = 5

kwargs={'startangle':270, 
        'wedgeprops': {'edgecolor': outer_background_color, 'linewidth': FIGURE_WIDTH*0.17},  # Set edge width
        'textprops': {'fontsize': FIGURE_WIDTH*1.8},  # Increase font size of labels
        'rotatelabels':False,
        'labeldistance':1.03,
        'pctdistance':0.76,
        }

red_colors = [
    # "#4b1611","#5b1b15",
    "#6b1f18", "#7b241c", "#8b2920", "#9b2d23", 
    "#ab3227", "#bb372b", "#cb3b2e", "#d2473a", "#d6564a", 
    "#d9655a", "#dd746a", "#e1837a", "#e4928a", "#e8a09a", 
    "#ecafaa", "#efbeba", "#f3cdca", "#f6dcda", "#faebea"
]

green_colors = [
    # "#0e3f23","#124f2b",
    "#155f34", "#196f3d", "#1d7f46", 
    "#208f4f", "#249f57", "#27af60", "#2bbf69", "#2fcf72", 
    "#3ed37c", "#4ed787", "#5edb92", "#6ede9d", "#7ee2a8", 
    "#8ee6b3", "#9ee9bd", "#aeedc8", "#bef0d3", "#cef4de"
]
figsize=(FIGURE_WIDTH*2, FIGURE_WIDTH)
title_fontsize=FIGURE_WIDTH*2.1
threshold_to_consider_as_less_contributors=5

def add_border(image, border_size=1, border_color=(0, 0, 0)):
    # Add a border around the given image
    return ImageOps.expand(image, border=(border_size, border_size), fill=border_color)

def stitch_images_horizontally(images, border_size=1, border_color="white"):
    # Calculate dimensions for the stitched image including borders
    widths, heights = zip(*(add_border(i, border_size).size for i in images))
    total_width = sum(widths)
    max_height = max(heights) 

    # Create a new blank image with the total width and maximum height
    stitched_image = Image.new('RGB', (total_width, max_height), color=(0,0,0))  # White background
    x_offset = 0
    for img in images:
        # Add border to the current image
        bordered_img = add_border(img, border_size, border_color)
        # Paste each bordered image into the stitched image at the current x_offset
        stitched_image.paste(bordered_img, (x_offset, 0))
        x_offset += bordered_img.width
    return stitched_image

def stitch_images_vertically(images,node_type,mem_or_cpu):
    # Get the maximum width and total height of the input images
    border_size=1
    border_color="white"
    widths, heights = zip(*(add_border(i, border_size).size for i in images))
    max_width = max(widths)
    total_height = sum(heights)
    # Create a new blank image with the maximum width and total height

    text_image_height=40
    text_image = Image.new('RGB', (max_width, text_image_height), color=outer_background_color)
    draw = ImageDraw.Draw(text_image)
    txt = f"{node_type.title()} nodetype : {mem_or_cpu} usage comparison and analysis"
    x = max_width/8
    draw.text((x,0),text=txt,align="right",font_size=FIGURE_WIDTH*5.3, fill =(255, 255, 255)) #(max_width//2, text_image_height//2),
    images.insert(0,text_image)

    empty_text_image_height=60
    text_image = Image.new('RGB', (max_width-1, empty_text_image_height), color=outer_background_color)
    draw = ImageDraw.Draw(text_image)
    images.insert(0,text_image)

    stitched_image = Image.new('RGB', (max_width, total_height+empty_text_image_height+text_image_height))
    y_offset = 0
    for img in images:
        bordered_img = add_border(img, border_size, border_color)
        # Paste each image into the stitched image at the current y_offset
        stitched_image.paste(bordered_img, (0, y_offset))
        y_offset += bordered_img.height
    return stitched_image

def compare_dfs(main,prev,merge_on):
    main.rename(columns={'avg': 'avg_main'}, inplace=True)
    prev.rename(columns={'avg': 'avg_prev'}, inplace=True)

    merged_df = pd.merge(prev,main, on=merge_on, how='outer')
    merged_df.fillna(0,inplace=True)
    merged_df["absolute"] = merged_df["avg_main"]- merged_df["avg_prev"] 
    merged_df["relative"] = (merged_df["avg_main"]- merged_df["avg_prev"] )*100/merged_df["avg_prev"]
    merged_df=merged_df.sort_values(by='absolute', ascending=False)
    return merged_df

def autopct_format(values,mem_or_cpu,sign='+'):
    if mem_or_cpu=="memory":
        unit="GB"
    else:
        unit="cores"
    def my_format(pct):
        total = sum(values)
        val = round(float(pct*total/100),2)
        return '{:.1f}%\n({}{} {})'.format(pct,sign, val,unit)
    return my_format

def compress_less_contributors(df,app_or_cont):
    sum_absolute = df["absolute"].sum()
    df["contributions"] = df["absolute"]*100/sum_absolute
    less_contri = df[df["contributions"]<threshold_to_consider_as_less_contributors]
    new_df = df[df["contributions"]>=threshold_to_consider_as_less_contributors]
    new_df=new_df._append({app_or_cont:f"others ({len(less_contri)})","absolute":less_contri["absolute"].sum()},ignore_index=True)
    return new_df

def compress(val):
    last = val.split('/')[-1]
    if len(last)>30:
        last = last.split('-')[-1]
    last=last.capitalize()
    return last

def get_piechart(nodetype,df,mem_or_cpu,app_cont_pod):
    if mem_or_cpu=="memory":unit="GB"
    else:unit="cores"

    fig, axs = plt.subplots(1, 2, figsize=figsize) 

    if not df.empty:
        increased = df[df["absolute"] > 0][[app_cont_pod,"absolute"]]
        decreased = df[df["absolute"] < 0][[app_cont_pod,"absolute"]]
        # df.to_csv(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_cont_pod}_{nodetype}.csv")
    else:
        increased = pd.DataFrame({})
        decreased = pd.DataFrame({})
    
    
    if not increased.empty:
        sum_app_increased = round(sum(increased["absolute"]),2)
        increased = compress_less_contributors(increased,app_cont_pod)

        axs[0].pie(increased['absolute'], labels=increased[app_cont_pod],autopct=autopct_format(increased['absolute'],mem_or_cpu),colors=red_colors, **kwargs)
        title_increased = f'{app_cont_pod.title()}s contributing to increase in \n{mem_or_cpu} for {nodetype} nodetype (+{sum_app_increased} {unit} ↑)'
        axs[0].set_title(title_increased, fontsize=title_fontsize)
    else:
        axs[0].pie([],[])
        axs[0].set_title(f"No {app_cont_pod.title()}s found contributing to \nincrease in {mem_or_cpu} for {nodetype} nodetype", fontsize=title_fontsize)
        axs[0].set_facecolor(outer_background_color)  # Set the background color to light gray
        axs[0].grid(False) 
        axs[0].spines['top'].set_visible(False)
        axs[0].spines['right'].set_visible(False)
        axs[0].spines['bottom'].set_visible(False)
        axs[0].spines['left'].set_visible(False)

    if not decreased.empty:
        sum_app_decreased = round(sum(decreased["absolute"]),2)
        decreased=decreased.sort_values(by="absolute",ascending=True)
        decreased = compress_less_contributors(decreased,app_cont_pod)
        decreased["absolute"] = decreased["absolute"].abs()

        axs[1].pie(decreased['absolute'], labels=decreased[app_cont_pod],autopct=autopct_format(decreased['absolute'],mem_or_cpu,'-'),colors=green_colors, **kwargs)
        title_decreased = f'{app_cont_pod.title()}s contributing to decrease in \n{mem_or_cpu} for {nodetype} nodetype ({sum_app_decreased} {unit} ↓)'
        axs[1].set_title(title_decreased, fontsize=title_fontsize)
    else:
        axs[1].pie([],[])
        axs[1].set_title(f"No {app_cont_pod.title()}s found contributing to \ndecrease in {mem_or_cpu} for {nodetype} nodetype", fontsize=title_fontsize)
        axs[1].set_facecolor(outer_background_color)  # Set the background color to light gray
        axs[1].grid(False) 
        axs[1].spines['top'].set_visible(False)
        axs[1].spines['right'].set_visible(False)
        axs[1].spines['bottom'].set_visible(False)
        axs[1].spines['left'].set_visible(False)
    each_piechart_title = f"{app_cont_pod.title()} level {mem_or_cpu.title() if mem_or_cpu=='memory' else mem_or_cpu.upper()}\n"
    if not df.empty:
        overall_absolute_increase_decrease = round(float(df["absolute"].sum()),2)
        overall_relative_increase_decrease = round((df["avg_main"].sum()-df["avg_prev"].sum())*100/df["avg_prev"].sum(),2)
        if overall_absolute_increase_decrease > 0:
            each_piechart_title += f"absolute increase: +{overall_absolute_increase_decrease} {unit}↑\n"
            each_piechart_title += f"relative increase: +{overall_relative_increase_decrease} %↑"
        else:
            each_piechart_title += f"absolute decrease: {overall_absolute_increase_decrease} {unit}↓\n"
            each_piechart_title += f"relative decrease: {overall_relative_increase_decrease} %↓"

    plt.suptitle(each_piechart_title,fontsize=title_fontsize+3)
    plt.gcf().set_facecolor(outer_background_color)
    plt.tight_layout()
    # plt.savefig(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_cont_pod}_{nodetype}.png")
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)  # Reset the buffer position
    image = Image.open(buffer)
    plt.close()
    if app_cont_pod=="container":short="container"
    elif app_cont_pod=="application":short="app"
    else:short=app_cont_pod

    if not increased.empty:
        increased["contributer"]=increased[app_cont_pod].apply(lambda x : x+" "+short)
        increased.drop(columns=app_cont_pod, inplace=True)
    if not decreased.empty:
        decreased["contributer"]=decreased[app_cont_pod].apply(lambda x : x+" "+short)
        decreased.drop(columns=app_cont_pod, inplace=True)
    return image,increased,decreased


def generate_piecharts(mem_or_cpu,main_dict,prev_dict):
    if mem_or_cpu=="memory":unit="GB"
    else:unit="cores"
    images = defaultdict(lambda:{})
    increased_df=defaultdict(lambda:pd.DataFrame({}))
    decreased_df=defaultdict(lambda:pd.DataFrame({}))
    for key,value in main_dict.items():
        if value == {}:
            print(f"Empty dict found for {mem_or_cpu}-{key}")
            continue
        app_cont_pod = key.split('_')[2]
        for nodetype,schema in value.items():
            current_df = pd.DataFrame(schema["data"])
            if current_df.empty:continue
            print(f"Analysing {app_cont_pod} level {mem_or_cpu} usage for {nodetype} nodetype ...")
            try:
                previous_df = pd.DataFrame(prev_dict[key][nodetype]["data"])
                merged_df = compare_dfs(current_df,previous_df,merge_on=["node_type",app_cont_pod])
                merged_df[app_cont_pod] = merged_df[app_cont_pod].apply(compress)
            except Exception as e:
                print(f"ERROR : {app_cont_pod} level {nodetype} nodetype doesnt exist for previous version") 
                merged_df = pd.DataFrame({})
            piechart,increased,decreased = get_piechart(nodetype,merged_df,mem_or_cpu,app_cont_pod)
            images[nodetype][app_cont_pod] = piechart
            increased_df[nodetype]=pd.concat([increased_df[nodetype], increased], ignore_index=True)
            decreased_df[nodetype]=pd.concat([decreased_df[nodetype], decreased], ignore_index=True)
    total_combined_dict =defaultdict(lambda:{})
    for ndtype,df in increased_df.items():
        if not df.empty:
            df = df.sort_values(by="absolute",ascending=False)
            df = df.head(5)
            df.drop(columns="contributions",inplace=True)
            string=""
            for row in df.itertuples(index=True, name='Pandas'):
                # Access columns by their names
                a_value = row.contributer
                b_value = round(row.absolute,2)
                string+=f'{a_value} : {b_value} {unit} ⬆️;   '
            total_combined_dict[ndtype]["Top 5 contributors to increase"]=string 
    for ndtype,df in decreased_df.items():
        if not df.empty:
            df = df.sort_values(by="absolute",ascending=False)
            df = df.head(5)
            df.drop(columns="contributions",inplace=True)
            string=""
            for row in df.itertuples(index=True, name='Pandas'):
                # Access columns by their names
                a_value = row.contributer
                b_value = round(row.absolute,2)
                string+=f'{a_value} : {b_value} {unit} ⬇️;   '
            total_combined_dict[ndtype]["Top 5 contributors to decrease"]=string
    total_combined_df = pd.DataFrame(total_combined_dict)
    total_combined_df=total_combined_df.T
    total_combined_df=total_combined_df.reset_index().rename(columns={'index': 'node_type'})
    return images,total_combined_df


def analysis_main(mem_main_dict,mem_prev_dict,cpu_main_dict,cpu_prev_dict,main_build_load_details="",prev_build_load_details=""):
    try:memory_images,memory_combined_df = generate_piecharts("memory",mem_main_dict,mem_prev_dict)
    except Exception as e:
        print(f"error occured while generating piecharts/dataframe for memory usages : {e}")

    try:cpu_images,cpu_combined_df = generate_piecharts("cpu",cpu_main_dict,cpu_prev_dict)
    except Exception as e:
        print(f"error occured while generating piecharts/dataframe for CPU usages : {e}")

    # memory_combined_df.to_csv("memory_combined_df.csv")  
    # cpu_combined_df.to_csv("cpu_combined_df.csv")    
    app_cont_pod_order = ["application","container","pod"]
    try:
        stitched_memory={}
        for nodetype,images in memory_images.items():
            images_to_stitch = []
            for app_cont_pod in app_cont_pod_order:
                try:
                    images_to_stitch.append(images[app_cont_pod])
                except:
                    images_to_stitch.append(get_piechart(nodetype,pd.DataFrame({}),"memory",app_cont_pod)[0])
            stitched_image = stitch_images_vertically(images_to_stitch,nodetype,"Memory")
            stitched_memory[nodetype]=stitched_image
            # path = f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{nodetype}_memory.png"
            # stitched_image.save(path)
    except Exception as e:
        print(f"error occured while vertical stitching memory piecharts : {e}")

    try:
        stitched_cpu={}
        for nodetype,images in cpu_images.items():
            images_to_stitch = []
            for app_cont_pod in app_cont_pod_order:
                try:
                    images_to_stitch.append(images[app_cont_pod])
                except:
                    images_to_stitch.append(get_piechart(nodetype,pd.DataFrame({}),"cpu",app_cont_pod)[0])
            stitched_image = stitch_images_vertically(images_to_stitch,nodetype,"CPU")
            stitched_cpu[nodetype]=stitched_image
            # path = f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{nodetype}_cpu.png"
            # stitched_image.save(path)
    except Exception as e:
        print(f"error occured while vertical stitching memory piecharts : {e}")

    try:
        load_details=f'{main_build_load_details["build"]}_run{main_build_load_details["run"]}   VS  {prev_build_load_details["build"]}_run{prev_build_load_details["run"]} \n Stack : {main_build_load_details["stack"]} \n {main_build_load_details["test_title"]}'
        final_images={}
        for node_type in stitched_memory.keys():
            print(node_type)
            final_stitched_image = stitch_images_horizontally([stitched_memory[node_type] , stitched_cpu[node_type]])

            text_image_height=60
            final_image_width,_ = final_stitched_image.size
            text_image = Image.new('RGB', (final_image_width, text_image_height), color=outer_background_color)
            draw = ImageDraw.Draw(text_image)
            
            draw.text((0,0),text=f"{load_details}",align="left",font_size=FIGURE_WIDTH*3, fill =(255, 255, 255)) #(max_width//2, text_image_height//2),
            draw.text((final_image_width/2.5,0),text=f"{node_type.title()} nodetype",align="center",font_size=FIGURE_WIDTH*7.35, fill =(255, 255, 255))
            text_image = add_border(text_image)
            final_stitched_image.paste(text_image, (2, 0))

            # path = f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{node_type}.png"
            # final_stitched_image.save(path)
            final_images[node_type] =final_stitched_image
            # final_stitched_image.show()
        return final_images,memory_combined_df,cpu_combined_df
    except Exception as e:
        print(f"error occured while horizotal stitching both memory and CPU images : {e}")
        return None, None, None
