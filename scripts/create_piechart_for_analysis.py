import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from PIL import Image
import io
from collections import defaultdict

# sns.set_theme(palette="dark", font="arial")
outer_background_color="#191b1f"
text_color="#FDFEFE"
sns.set(rc={"text.color": text_color})

kwargs={'startangle':270, 
        'wedgeprops': {'edgecolor': outer_background_color, 'linewidth': 1.0},  # Set edge width
        'textprops': {'fontsize': 18},  # Increase font size of labels
        'colors' : ['#196F3D','#21618C','#7B241C','#7D6608','#4A148C','#6E2C00','#880E4F',"#330066","#7D4D00"],
        'rotatelabels':False,
        'labeldistance':1.01,
        'pctdistance':0.8,
        }

figsize=(30, 12)
title_fontsize=22
threshold_to_consider_as_less_contributors=2

def stitch_images_horizontally(images):
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    # Create a new blank image with the total width and maximum height
    stitched_image = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for img in images:
        # Paste each image into the stitched image at the current x_offset
        stitched_image.paste(img, (x_offset, 0))
        x_offset += img.width
    return stitched_image

def stitch_images_vertically(images):
    # Get the maximum width and total height of the input images
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    # Create a new blank image with the maximum width and total height
    stitched_image = Image.new('RGB', (max_width, total_height))
    y_offset = 0
    for img in images:
        # Paste each image into the stitched image at the current y_offset
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.height
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
    else:
        increased = pd.DataFrame({})
        decreased = pd.DataFrame({})
    
    
    if not increased.empty:
        sum_app_increased = round(sum(increased["absolute"]),2)
        increased = compress_less_contributors(increased,app_cont_pod)

        axs[0].pie(increased['absolute'], labels=increased[app_cont_pod],autopct=autopct_format(increased['absolute'],mem_or_cpu), **kwargs)
        title_increased = f'{app_cont_pod}s contributing to {"increase".upper()} in {mem_or_cpu} usage for "{nodetype}" nodetype (+{sum_app_increased} {unit} ↑)'
        axs[0].set_title(title_increased, fontsize=title_fontsize)
    else:
        axs[0].plot([],[])
        axs[0].set_title(f"No {app_cont_pod}s found contributing to increase in {mem_or_cpu} for {nodetype} nodetype", fontsize=title_fontsize)
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

        axs[1].pie(decreased['absolute'], labels=decreased[app_cont_pod],autopct=autopct_format(decreased['absolute'],mem_or_cpu,'-'), **kwargs)
        title_decreased = f'{app_cont_pod}s contributing to {"decrease".upper()} in {mem_or_cpu} usage for "{nodetype}" nodetype ({sum_app_decreased} {unit} ↓)'
        axs[1].set_title(title_decreased, fontsize=title_fontsize)
    else:
        axs[1].plot([],[])
        axs[1].set_title(f"No {app_cont_pod}s found contributing to decrease in {mem_or_cpu} for {nodetype} nodetype", fontsize=title_fontsize)
        axs[1].set_facecolor(outer_background_color)  # Set the background color to light gray
        axs[1].grid(False) 
        axs[1].spines['top'].set_visible(False)
        axs[1].spines['right'].set_visible(False)
        axs[1].spines['bottom'].set_visible(False)
        axs[1].spines['left'].set_visible(False)

    plt.gcf().set_facecolor(outer_background_color)
    plt.tight_layout()
    plt.savefig(f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{mem_or_cpu}_{app_cont_pod}_{nodetype}.png")
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)  # Reset the buffer position
    image = Image.open(buffer)
    plt.close()
    return image


def generate_piecharts(mem_or_cpu,main_dict,prev_dict):
    images = defaultdict(lambda:{})
    for key,value in main_dict.items():
        if value == {}:
            print(f"Empty dict found for {mem_or_cpu}-{key}")
            continue
        app_cont_pod = key.split('_')[2]
        for nodetype,schema in value.items():
            current_df = pd.DataFrame(schema["table"])
            if current_df.empty:continue
            print(f"Analysing {app_cont_pod} level {mem_or_cpu} usage for {nodetype} nodetype ...")
            try:
                previous_df = pd.DataFrame(prev_dict[key][nodetype]["table"])
                merged_df = compare_dfs(current_df,previous_df,merge_on=["node_type",app_cont_pod])
                merged_df[app_cont_pod] = merged_df[app_cont_pod].apply(compress)
            except Exception as e:
                print(f"ERROR : {app_cont_pod} level {nodetype} nodetype doesnt exist for previous version") 
                merged_df = pd.DataFrame({})
            piechart = get_piechart(nodetype,merged_df,mem_or_cpu,app_cont_pod)
            images[nodetype][app_cont_pod] = piechart
    return images


def analysis_main(mem_main_dict,mem_prev_dict,cpu_main_dict,cpu_prev_dict):
    memory_images = generate_piecharts("memory",mem_main_dict,mem_prev_dict)
    cpu_images = generate_piecharts("cpu",cpu_main_dict,cpu_prev_dict)

    app_cont_pod_order = ["application","container","pod"]

    stitched_memory={}
    for nodetype,images in memory_images.items():
        stitched_image = stitch_images_horizontally([images[app_cont_pod] for app_cont_pod in app_cont_pod_order])
        stitched_memory[nodetype]=stitched_image

    stitched_cpu={}
    for nodetype,images in cpu_images.items():
        stitched_image = stitch_images_horizontally([images[app_cont_pod] for app_cont_pod in app_cont_pod_order])
        stitched_cpu[nodetype]=stitched_image

    for node_type in stitched_memory.keys():
        print(node_type)
        vertical_stitched_image = stitch_images_vertically([stitched_memory[node_type] , stitched_cpu[node_type]])
        path = f"/Users/masabathulararao/Documents/Loadtest/save-report-data-to-mongo/scripts/csv/{nodetype}.png"
        vertical_stitched_image.save(path)
        vertical_stitched_image.show()
