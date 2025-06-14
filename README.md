# ParshaCast Project

## Overview
ParshaCast is a Python-based application designed to automate the process of downloading, processing, and filtering lecture data from Yutorah.org. The application retrieves lectures from specified rabbis, enriches the data, and prepares it for podcast generation in XML format.

## Project Structure
```
parshacast
├── src
│   └── main.py          # Entry point for the application
├── data
│   ├── rabbis_lectures.csv  # Initial lecture data
│   ├── yutorah-shiurim.txt  # Enriched lecture data
│   └── podcast_input.txt     # Final output for podcast generation
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Installation
To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd parshacast
pip install -r requirements.txt
```

## Usage
1. **Download Lectures**: Run the `main.py` script to fetch lectures from Yutorah.org based on the specified rabbis and subcategory ID. This will generate the `rabbis_lectures.csv` file.
   
2. **Process Data**: The `main.py` script will also convert the `rabbis_lectures.csv` into `yutorah-shiurim.txt`, adding additional fields for each lecture.

3. **Generate Podcast XML**: Finally, the processed data will be used to create the `podcast_input.txt` file, which is structured for XML conversion, ready for podcast generation.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.