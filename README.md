## FeatureTools for Spark (featuretools4s)

### 1. What's FeatureTools? 
FeatureTools is a Python library open-sourced by MIT's 
FeatureLab aiming to automate 
the process of feature engineering in Machine Learning 
applications. 

Please visit the [official website](https://docs.featuretools.com/index.html)
for more details about FeatureTools. 

*FeatureTools4S* is a Python library written by me aiming to scale 
FeatureTools with **Spark**, making it capable of generating 
features for billions of rows of data, which is usually 
considered impossible to process on single machine using 
original FeatureTools library with Pandas. 

*FeatureTools4S* provides **almost the same** API as original 
FeatureTools, which make its users completely free of transferring 
between FeatureTools and FeatureTools4S. **Hence we suggest the readers 
first to learn FeatureTools and then you can easily work on FeatureTools4S.**

  