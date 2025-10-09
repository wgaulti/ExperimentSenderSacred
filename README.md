# Experiment Sender to Sacred

This tool is a Graphical User Interface developped in Python using TkinterCustom GUI library. It allows users to send their experiments results stored locally to a MongoDB Sacred Database and if needed to send heavy files to a MinIO Server and/or a file path destination.

## Prerequisites
- Have a Python environment installed on your computer
- Have a Mongo database running on a server or locally and have access to it
- Optionnal: Have a MinIO server

## Set up project
1. Get the project, either by downloading the zip from Github or cloning the repo:
```
git clone https://github.com/DreamRepo/ExperimentSenderSacred.git
```
2. Open a terminal and go inside the ExperimentSenderSacred folder

3. Set up a Python Virtual Environment (Recommended) and activate it
```
python -m venv .venv
```
```
.venv\Scripts\activate
```
4. Install requirements
```
pip install -r requirements.txt
```

## Run the app

Run the following command in the terminal:
```
python app.py
```
The app window should open

## Set up MongoDB connection (and MinIO if needed)
Enter your database credentials to send your experiments to your database, there is a button to test if the connection can be established between the app and your database.

## Set up experiment files configuration
### Select your experiment folder
You have to have a folder per experiment, and the name of that folder should be the same as the experiment.
### Select the files you want to use for each of the category
#### **Config**
This is the configuration of the experiment (name, experimental conditions, instrument, etc.). It can be an Excel file, a csv or a json file. If you select a json file, you have the option to flatten it:
```json
{
    "experiment": {
        "name": "Experiment1",
        "duration": {
            "time": 3200,
            "unit": "seconds"
        }
    }
}
```
will become:
```json
{
    "experiment_name": "Experiment1",
    "experiment_duration_time": 3200,
    "experiment_duration_unit": "seconds"
}
```
In case of a csv or Excel file, the file must have this format with no header, directly the parameters and their values:
| config.csv     |        |
|---------------|------------------|
| param1   | 1     |
| param2   | val2      |
| param3   | 3      |
| ...   | ...      |

#### **Results**
This are the results values of the experiment. It can be an Excel sheet from Excel file, a csv or a json file (no flatten option for the json).

In case of a csv or Excel file, the file must have this format with no header, directly the parameters and their values:
| results.csv     |        |
|---------------|------------------|
| result1   | 1     |
| result2   | val2      |
| result3   | 3      |
| ...   | ...      |

#### **Metrics** 
This are the series to plot. It can be an Excel or a csv file. It will plot all the columns in the specified spreadsheet. If the columns have a name, tick Column header, if there is a x-axis column, tick the option and then select the x-axis column. Then tick the columns that are going to be plotted in the database.

#### **Raw data**
This is for the heavy files that are going to be sent to the database. You can either select a single file in the folder or a folder in the folder. If you select a folder, you can select the files you want to transfer. You can choose to send the files to a local path or a remote drive accessible on your computer path and/or a MinIO server.
When you send a file it will be organized according to the following strategy:
- The selected files will be renamed as follows:
`video.tiff` will be saved as:
    - `video/[experiment_name_hash]_[datetime]_video.tiff` if the experiment folder name contains a datetime.
    - `video/[experiment_name_hash]_video.tiff` if the experiment folder name does not contain a datetime.

The hash method is defined in `service/hash.py`. It takes the complete name folder and hash it into a 7 characters (letters and numbers only) string.

#### **Artifacts**
This are the light files (< 50MB) that can be sent to the MongoDB database. The sending strategy is the same as described for Raw data. Those files can be directly accessed from Omniboard. It is not recommended to store large files as artifacts as it greatly impacts database performance.

## Send experiments to the database

Once the experiment pattern is set up, the experiment can be sent to the database by clicking the **Send experiment** button. You can all also send experiments in folders from the same parent folder. To do that, the structure of the experiments should be exactly the same and the experiment folder name is the only thing that should change. File names, columns names, sheet names should all be the same in the folders.

#### Example
```
Parent folder
├── 01-01-25_10-20-03_Experiment1
│   ├── config.json
│   ├── results.csv
│   ├── metrics.xlsx
│   ├── capture.png
│   └── raw_data
│       ├── frames.tiff
│       └── video.mp4
│ 
└── 02-02-25_11-10-07_Experiment2
    ├── config.json
    ├── results.csv
    ├── metrics.xlsx
    ├── capture.png
    └── raw_data
        ├── frames.tiff
        └── video.mp4
```
In this example, you first select the **01-01-25_10-20-03_Experiment1** folder, you put the configuration for this experiment. Then you tick the option **Send multiple experiments** all the experiment folders will be selected (for this example **01-01-25_10-20-03_Experiment1** and **02-02-25_11-10-07_Experiment2**). If they have the exact same configuration, all the selected experiments will be sent to the database.