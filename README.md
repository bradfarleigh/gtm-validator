# How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run  app.py
   ```

Run `python _export.py` to dump out a file which contains all scripts which can be loaded to a LLM for analysis

# Bugs
* Fix TikTok / FB lookup - we need to match cvt_XXXX_(.*) on the event with customTemplate.TemplateId = $1 and return the customTemplate.name 

# Todo

* Tag naming convention check vs best practice
* Check vs defined tracking code numbers (FB TT etc)
* GA4 event name checks
* Checkboxes on what to audit
* Get container name from json
* export action points
* verbose action points (i.e. tag X needs X)
* Login
   * Custom naming rules
* consent mode check
* cookie consent detection
   * check tags are hooked in properly