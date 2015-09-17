# Web Tools
## Browser-as-a-Service

``web-tools`` is a StackHut service that performs several web-developer related functions. 

It's powered by,

* [PhantomJS](http://phantomjs.org/)
* [Selenium](http://www.seleniumhq.org/).

It uses these to provide a screen-shotting service that works for JS-heavy sites but will be expanded in the future. 


## Usage

### Service Interface (`api.idl`)

#### `Default` Interface

* `renderWebpage(url string, width int, height int) string`
    
    screenshot a website, providing width and height of browser


### Example

This example shows calling the service method `stackhut/web-tools/Default.renderWebpage` using the Python client libraries to add a comment to an image and generate a meme.

```python
import stackhut_client as client
web_tools = client.SHService('stackhut', 'web-tools')
render_url = web_tools.Default.renderWebpage("http://www.stackhut.com", 1024, 768)
```

## Detailed Documentation

### Overview

This Python-based service demonstrates the following features,

* OS dependencies
* Embedding resource files within a service
* Custom binaries and dependencies
* Running arbitrary Docker build commands

We also recommend looking at other, more detailed, examples of using StackHut to [convert PDF files](https://github.com/StackHut/pdf-tools) and [process images](https://github.com/StackHut/image-process).

The `renderWebpage` function in this service operates by configuring a headless browser and remotely rendering the referenced URL into to a image and uploading the result to a URL that is returned to the user.

To accomplish this we need to configure the service within the `Hutfile.yaml` to include the necessary OS/language libraries and to bundle resource files, and make use of the [StackHut runtime library](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) within our `app.py` service code to handle files.


### API Definition (`api.idl`)

The API definition below defines the publicly accessible entry-points to the service that can be called from clients, e.g. client-side JS or mobile applications. Here we declare several functions that operate on images and return the result. 
The syntax is somewhat similar to defining an interface in Java but using basic JSON types - this is described further in the [StackHut documentation](http://stackhut.readthedocs.org/en/latest/creating_service/app_structure.html#interface-definition-api-idl).


```java
interface Default {
    // screenshot a website, providing width and height of browser
    renderWebpage(url string, width int, height int) string
}
```


### Service Configuration (`Hutfile.yaml`)

The `Hutfile.yaml` listed below follows the format described in the [documentation](http://stackhut.readthedocs.org/en/latest/creating_service/service_structure.html#hutfile): specifying the base OS (e.g. Fedora, Debian, etc.), the language stack (e.g. Python, NodeJS, etc.), and so on. 

Now let's look at the `os_deps` field, this is a list of OS packages that are to be installed and embedded within the image - packages one would install using `apt-get` or `yum` within a Linux distribution. 
Here we configure the service to include the `GraphicsMagick` and `python3-pillow` package from the Fedora package repository.

Finally let's look at the `files` field, this is a list of files within the project directory that you wish to package up within the service for deployment.
This list can be either individual files or directories, in which case the entire contests of the directory is included. (Note, you must explicitly list additional files within this field to ensure they exist during testing and deployment. By default only the basic project files are packaged up.)


```yaml
# Service name (a combination of lower case letters, numbers, and dashes)
name: web-tools

# GitHub source repo link (optional)
github_url: https://github.com/StackHut/web-tools

# Service description
description: Web dev tools inc. a headless browser written in Selenium

# The service dependencies, in terms of the base OS and language runtime
baseos: fedora
stack: python

# Persist the service between requests
persistent: False

# Restrict service access to authenticated users
private: False

# a list of files we wish to copy into the image
files:
    - phantomjs-2.0.1-bin
    - libicu-4.2.1-9.1.el6_2.x86_64.rpm  # wget from http://mirror.centos.org/centos/6/os/x86_64/Packages/libicu-4.2.1-9.1.el6_2.x86_64.rpm

os_deps:
    - freetype
    - fontconfig
    - libjpeg
    - libpng
    - libpng12
    - urw-fonts

docker_cmds:
    - RUN rpm -iv --force libicu-4.2.1-9.1.el6_2.x86_64.rpm
```

### Application Code (`app.py`) 

This application code show below and in [`app.py`](https://github.com/StackHut/web-tools/blob/master/app.py) forms the service entry-points exposed by the `web-tools` service, with the methods and parameters matching those described above and in the `api.idl`.
This is standard [Python 3](http://www.python.org) code however there are a few important points to note around file handling and shelling out to external commands.

```python
import stackhut
from selenium import webdriver

class Default(stackhut.Service):
    def __init__(self):
        pass

    def renderWebpage(self, url, width, height):
        driver = webdriver.PhantomJS(stackhut.root_dir + "/phantomjs-2.0.1-bin") # or add to your PATH
        driver.set_window_size(width, height) # optional
        driver.get(url)

        driver.save_screenshot('screen.png') # save a screenshot to disk
        return stackhut.put_file('screen.png')

# export the services here
SERVICES = {"Default": Default()}
```



#### File Handling

We use the [StackHut runtime functions](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) to aid file handling within the service - this includes the functions `stackhut.download_file()` and `stackhut.put_file()` that transparently download and upload files respectively to cloud storage. Files are processed within the current working directory, this is unique to each request and flushed upon request completion. Files themselves live on the cloud for approximately a few hours before being removed.

#### Running Commands

As mentioned previously, we indicating a dependency upon the `GraphicsMagick` Fedora package within our service. This package installs the `gm` binary that can be used within the service.

To process images with GraphicsMagick we need to be able to call the `gm` binary from within our service function. Generally this is done by using your language's process management features to execute the binary as a sub-process. 
When using Python we recommend and use the [sh](https://amoffat.github.com/sh) package that presents a simple way to call external binaries from within your service. 
However it's important to note that techniques exist in every language to call an binary embedded within the service - your service is running in a secure, custom container and you can do anything as needed inside it.


