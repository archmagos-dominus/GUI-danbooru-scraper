from tkinter import *
import tkinter.ttk as tkk
from tkinter import messagebox
import tkinter as tk
import json
import os
from pathlib import Path
import requests
from PIL import ImageTk,Image

global img
global current_image
image_index = 0
folder_size = 0

root = Tk()
root.title("GUI Scraper")
root.geometry("400x400")

def get_data():
    if os.path.exists('data.json'):
        f = open('data.json')
        data = json.load(f)
        f.close()
    else:
        data = {
            "output_path": "output/",
            "url": "https://danbooru.donmai.us",
            "page_limit": 5,
            "api_key": "",
            "login": "",
            "file_size": "large_file_url",
            "small_fs": "file_url"
        }
        with open('data.json', "w") as file:
            json.dump(data, file)
    return data

def get_screen_size():
    test = tk.Tk()
    test.update_idletasks()
    test.attributes('-fullscreen', True)
    test.state('iconic')
    geometry = test.winfo_geometry()
    test.destroy()
    size = geometry.split("+")
    return size[0]

def save_data():
    login = login_var.get()
    token = token_var.get()
    output = out_path_var.get()
    tags = tags_var.get()
    page_limit = page_limit_var.get()
    maxFS = maxFS_var.get()
    g = g_var.get()
    s = s_var.get()
    q = q_var.get()
    e = e_var.get()
    translation = translation_var.get()
    data = get_data()
    progress_bar["maximum"] = (page_limit-1)*100

    if login: data["login"] = login
    if token: data["api_key"] = token
    if output: data["output_path"] = output
    if page_limit: data["page_limit"] = page_limit
    if maxFS==1:
        data["file_size"] = 'large_file_url'
    else:
        data["file_size"] = "file_url"
    rating_tag = ""
    multiple_ratings = False
    if g:
        rating_tag += 'g'
        multiple_ratings = True
    if s:
        if multiple_ratings:
            rating_tag+=',s'
        else:
            rating_tag+='s'
            multiple_ratings = True
    if q:
        if multiple_ratings:
            rating_tag+=',q'
        else:
            rating_tag+='q'
            multiple_ratings = True
    if e:
        if multiple_ratings:
            rating_tag+=',e'
        else:
            rating_tag+='e'
    if rating_tag:
        rating_tag = 'rating:'+ rating_tag
        tag_data = f"{tags} {rating_tag}"
    else:
        tag_data = tags
    with open("data.json", "w") as file:
        json.dump(data, file)
    main_scraper(tag_data, translation)

def main_scraper(tag_data,translation):
    #get data fron json
    data = get_data()

    # create folder if not
    os.makedirs(data['output_path'], exist_ok=True)
    data_file_name = data['output_path'] + 'image_data.json'
    i = 0
    j = 0

    # get posts
    for post in getPosts(tag_data, data):
        if "file_url" not in post:
            continue
        url_path = post[data["file_size"]]
        filename = Path(url_path).name
        img_file = data['output_path'] + filename
        if not os.path.exists(img_file):
            print(f"Downloading {img_file}")
            i += 1
            current_image = i
            print(f"Indexed {i} images")
            req = requests.get(url_path, stream=True)
            save_image(req, img_file)
            notes = ""
            if translation:
                for tag in post["tag_string"].split():
                    if tag == "translated":
                        notes = getNotes(data, post)
                        j += 1
                        print(f"Indexed {j} translations")
            storeImageData(post, notes, filename, data_file_name)
        progress_bar.step(1)
        root.update()
    messagebox.showinfo("Results", f"Scraped {i} files and {j} translations.")
    progress_bar["value"] = 0

def getPosts(tags, data):
    for i in range(1, data["page_limit"]):
        #create parameter payload
        params = {
            "tags": tags,
            "page": i,
            "login": data["login"],
            "api_key": data["api_key"],
            "limit": 100
        }
        #make request
        req = requests.get(f'{data["url"]}/posts.json', params=params)
        content = req.json()
        if content == []:
            return
        if "success" in content and not content["success"]:
            raise Exception("Danbooru API: " + content["message"])
        yield from content

def getNotes(data,post):
    params = {
        "login": data["login"],
        "api_key": data["api_key"],
        "search[post_id": post["id"]
    }
    req = requests.get(f"{data['url']}/notes.json", params=params)
    content = req.json()
    notes = ""
    index = 1
    for note in content:
        notes = notes +  f'{index}: "{note["body"]}" '
        index += 1
    return notes

def save_image(stream, path):
    with Path(path).open('wb') as f:
        for bytes in stream.iter_content(chunk_size=128):
            f.write(bytes)

def storeImageData(post, notes, filename, data_file_name):
    if os.path.exists(data_file_name):
        with open(data_file_name, 'r+') as file:
            image_data = {
                "filename": filename,
                "artist": post["tag_string_artist"],
                "characters": post["tag_string_character"],
                "rating": post["rating"],
                "tags": post["tag_string"],
                "translation": notes
            }
            # First we load existing data into a dict.
            file_data = json.load(file)
            # Join new_data with file_data inside emp_details
            file_data.append(image_data)
            # Write json file
            with open(data_file_name, "w") as file:
                json.dump(file_data, file)
    else:
        with open(data_file_name, "w") as file:
            image_data = [{
                "filename": filename,
                "artist": post["tag_string_artist"],
                "characters": post["tag_string_character"],
                "rating": post["rating"],
                "tags": post["tag_string"],
                "translation": notes
            }]
            json.dump(image_data, file)

def get_image_data(folder_path):
    file_path = folder_path + 'image_data.json'
    if not os.path.exists(file_path):
        return False
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data

def prev_entry(image_view_window):
    global image_index
    global folder_size
    image_index -= 1
    if image_index < -folder_size:
        image_index = 0
    print(image_index)
    image_view_window.destroy()
    view_saved_illustrations()


def next_entry(image_view_window):
    global image_index
    global folder_size
    image_index += 1
    if image_index > folder_size-1:
        image_index = 0
    print(image_index)
    image_view_window.destroy()
    view_saved_illustrations()


def delete_entry():
    return

def modify_entry():
    return

def view_saved_illustrations():
    global size
    global folder_size
    data = get_data()
    folder_path = data["output_path"]
    image_data = get_image_data(folder_path)
    if not image_data:
        return messagebox.showinfo("No image data found", "File 'image_data.json' not present in the output path.")
    #create gui
    folder_size = len(image_data)
    image_view_window = tk.Toplevel()
    image_view_window.title("Output viewer")
    image_view_window.geometry(size)
    main_size = size.split("x")
    main_width = int(main_size[0])
    main_height = int(main_size[1])
    ##canvas for image
    canvas = Canvas(image_view_window, width=(main_width-340), height=(main_height-100),background='#5B5B66')
    canvas.place(x=20,y=20)

    ##labels for tags
    filename_label = Label(image_view_window,text="Username").place(x=main_width-300,y=20)
    artist_label = Label(image_view_window,text="Artist").place(x=main_width-300,y=50)
    character_label = Label(image_view_window,text="Character").place(x=main_width-300,y=80)
    ratings_label = Label(image_view_window,text="Rating").place(x=main_width-300,y=110)
    tag_label = Label(image_view_window,text="Tags").place(x=main_width-300,y=140)
    translations_label = Label(image_view_window,text="Translation").place(x=main_width-300,y=170)

    #inputs for tags
    filename_var = tk.StringVar()
    artist_var = tk.StringVar()
    character_var = tk.StringVar()
    ratings_var = tk.StringVar()
    tag_var = tk.StringVar()
    translations_var = tk.StringVar()

    filename_input = tk.Entry(image_view_window, width=20, textvariable=filename_var)
    filename_input.insert(0,image_data[image_index]["filename"])
    filename_input.place(x=main_width-160, y=20)
    artist_input = tk.Entry(image_view_window, width=20, textvariable=artist_var)
    artist_input.insert(0,image_data[image_index]["artist"])
    artist_input.place(x=main_width-160, y=50)
    character_input = tk.Entry(image_view_window, width=20, textvariable=character_var)
    character_input.insert(0,image_data[image_index]["characters"])
    character_input.place(x=main_width-160, y=80)
    ratings_input = tk.Entry(image_view_window, width=20, textvariable=ratings_var)
    ratings_input.insert(0,image_data[image_index]["rating"])
    ratings_input.place(x=main_width - 160, y=110)
    tag_input = tk.Entry(image_view_window, width=20, textvariable=tag_var)
    tag_input.insert(0,image_data[image_index]["tags"])
    tag_input.place(x=main_width-160, y=140)
    translations_input = tk.Entry(image_view_window, width=20, textvariable=translations_var)
    translations_input.insert(0,image_data[image_index]["translation"])
    translations_input.place(x=main_width-160, y=170)

    ##button for next, prev, and delete (+modify?)
    prev_button = Button(image_view_window, text="<<", command=lambda:prev_entry(image_view_window)).place(x=main_width-300, y=main_height-200)
    delete_button = Button(image_view_window, text="Delete", command=delete_entry).place(x=main_width-225, y=main_height-200)
    modify_button = Button(image_view_window, text="Modify", command=modify_entry).place(x=main_width-150, y=main_height-200)
    next_button = Button(image_view_window, text=">>", command=lambda:next_entry(image_view_window)).place(x=main_width-75, y=main_height-200)
    exit_window = Button(image_view_window, text="Close window", command=image_view_window.destroy).place(x=main_width-295, y=main_height-100)



    #show first image in data file
    img_path = image_data[image_index]["filename"]
    full_path = folder_path+img_path
    image_temp = Image.open(full_path)
    ratio = image_temp.width / image_temp.height
    width = main_width - 340
    img_w = width
    height = main_height - 100
    img_h = height
    print(f"{img_w} x {img_h}")
    print(f"{image_temp.width} x {image_temp.height}")
    if image_temp.height > height:
        img_w = height * ratio
        img_h = height
        if image_temp.width > width:
            img_w = width
            img_h = img_w/ratio
    if image_temp.width > width:
        img_w = width
        img_h = width/ratio
        if image_temp.height > height:
            img_h = height
            img_w = img_h * ratio
    if image_temp.width <= width and image_temp.height <= height:
        img_h = image_temp.height
        img_w = image_temp.width
    #upscaling?
    image_tmp = image_temp.resize((int(img_w),int(img_h)))
    print(f"{img_w} x {img_h}")
    img = ImageTk.PhotoImage(image_tmp)
    canvas.create_image(0, 0, anchor=NW, image=img)
    image_view_window.mainloop()


#checkmark variables
login_var=tk.StringVar()
token_var=tk.StringVar()
out_path_var=tk.StringVar()
tags_var=tk.StringVar()
page_limit_var=tk.IntVar()


maxFS_var = tk.IntVar()
g_var = tk.IntVar()
s_var = tk.IntVar()
q_var = tk.IntVar()
e_var = tk.IntVar()
translation_var = tk.IntVar()

# the labels
username_label = Label(root,text="Username").place(x=20,y=20)
apiKey_label = Label(root,text="API Key").place(x=20,y=50)
output_label = Label(root,text="Output location").place(x=20,y=80)
tags_label = Label(root,text="Tags").place(x=20,y=110)
pageLim_label = Label(root,text="Page Limit").place(x=20,y=140)
translation_label = Label(root,text="Translation").place(x=20,y=170)
maxFS_label = Label(root,text="Large Image Size").place(x=20,y=200)
rating_label = Label(root,text="Rating:").place(x=20,y=230)

data_main = get_data()
#the inputs fields
username_input = Entry(root,width=25,textvariable=login_var)
username_input.insert(0,data_main["login"])
username_input.place(x=210,y=20)
apiKey_input = Entry(root,width=25,textvariable=token_var)
apiKey_input.insert(0,data_main["api_key"])
apiKey_input.place(x=210,y=50)
output_input = Entry(root,width=25,textvariable=out_path_var)
output_input.insert(0,data_main["output_path"])
output_input.place(x=210,y=80)
tags_input = Entry(root,width=25,textvariable=tags_var).place(x=210,y=110)
pageLim_spinbox = Spinbox(root, from_= 0, to = 5000,textvariable=page_limit_var).place(x=210,y=140)
tranlation_check = Checkbutton(root, text = "",variable = translation_var,onvalue = True,offvalue = False,height = 1,width = 1).place(x=210,y=170)
maxFS_check = Checkbutton(root, text = "",variable = maxFS_var,onvalue = True,offvalue = False,height = 1,width = 1).place(x=210,y=200)
rating_check_g = Checkbutton(root, text = "General",variable = g_var,onvalue = True,offvalue = False,height = 2,width = 8).place(x=20,y=260)
rating_check_s = Checkbutton(root, text = "Sensitive",variable = s_var,onvalue = True,offvalue = False,height = 2,width = 8).place(x=100,y=260)
rating_check_q = Checkbutton(root, text = "Questionable",variable = q_var,onvalue = True,offvalue = False,height = 2,width = 12).place(x=180,y=260)
rating_check_e = Checkbutton(root, text = "Explicit",variable = e_var,onvalue = True,offvalue = False,height = 2,width = 8).place(x=290,y=260)

#progress bar
progress_bar = tkk.Progressbar(root, orient=HORIZONTAL, mode='determinate')
progress_bar.place(x=20,y=300,width=350)

#the buttons
submit_button = Button(root,text="Scrape",command=save_data).place(x=100,y=350)
view_button = Button(root,text="View ouput", command=view_saved_illustrations).place(x=200,y=350)

size = get_screen_size()
root.mainloop()
