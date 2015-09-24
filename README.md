# Web Tools
## Browser-as-a-Service

``web-tools`` is a StackHut service that screenshots websites. This is a common task that is tricky to build on a regular server, and suits itself particularly well to StackHut.

It's powered by,

* [PhantomJS](http://phantomjs.org/),
* [Selenium](http://www.seleniumhq.org/),


## Usage

### Service Interface (`api.idl`)

#### `Default` Interface

* `renderWebpage(url string, width int, height int) string`
    
    screenshot a website, providing width and height of browser

### Example

This example calls the method `stackhut/web-tools/Default.renderWebpage` using the JavaScript client libraries. This will screenshot the given website, and return a URL to an image of the website.

```javascript
let client = require('stackhut-client');
let service = client.SHService('stackhut', 'web-tools');
let result = service.Default.renderWebpage("https://stackhut.com",1280,359);
```

## Detailed Documentation

### Overview

This Python-based service demonstrates the following features,

* OS dependencies
* Embedding and accessing resource files within a service
* Custom binaries and dependencies
* Running arbitrary [Docker build](https://docs.docker.com/reference/builder/) commands

The `renderWebpage` function in this service operates by configuring a headless browser and remotely rendering the referenced URL into to a image, uploading the result, and returning a URL to the uploaded image.

Firstly, we need to specify the API into our service in `api.idl`.

Secondly, we need to configure the service within the `Hutfile.yaml`. This will include the necessary OS/language libraries, bundle resource files, and run the arbitrary shell commands which our service needs. 

We then write our service as a regular Python class in `app.py`, which will make use of the [StackHut runtime library](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) to handle files and embedded resources.

### API Definition (`api.idl`)

The API definition below defines the publicly accessible entry-points to the service that can be called from clients, e.g. client-side JS or mobile applications. 

The syntax is somewhat similar to defining an interface in Java but using basic JSON types - this is described further in the [StackHut documentation](http://stackhut.readthedocs.org/en/latest/creating_service/app_structure.html#interface-definition-api-idl).

We have one function we want to call: renderWebpage. So let's add it's signature.

```java
interface Default {
    // screenshot a website, providing width and height of browser
    renderWebpage(url string, width int, height int) string
}
```


### Service Configuration (`Hutfile.yaml`)

The `Hutfile.yaml` listed below follows the format described in the [documentation](http://stackhut.readthedocs.org/en/latest/creating_service/service_structure.html#hutfile): specifying the base OS (e.g. Fedora, Debian, etc.), the language stack (e.g. Python, NodeJS, etc.), and so on. 

For this particular service we set the `persistent` flag to be `False`, causing the StackHut platform to construct the service in response to a request and destroy it afterwards. This is a conscious decision, as  the `PhantomJS` binary can be unstable over time; making the service stateless allows us to combat this and guarantee scalability.

If we look at the `os_deps` field, we will see a list of OS packages that are to be installed and embedded within the image - packages that one would install using `apt-get` or `yum` within a Linux distribution. Here we configure the service to include a range of Linux system libraries from the Fedora package repository which PhantomJS requires.

Within the `files` field we include a list of files within the project directory that you wish to package up within the service for deployment.

This list can be either individual files or directories, in which case the entire contests of the directory is included. (Note, you must explicitly list additional files within this field to ensure they exist during testing and deployment. By default only the basic project files are packaged up.)

In this case we include a set of custom binaries to run [PhantomJS](http://phantomjs.org/). PhantomJS is tricky to build, and is not not available within the OS package repositories, so we have to install it from the file itself.

Finally we include the `docker_cmds` field, this specifies a list of explicit, imperative, commands to be executed when constructing the Docker container. The available commands are those supported by Docker's [Dockerfile build system](https://docs.docker.com/reference/builder/). Here we use the `docker_cmds` field to explicitly install a RedHat Linux `.rpm` package inside the service that is required by `PhantomJS`.


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
    - libicu-4.2.1-9.1.el6_2.x86_64.rpm  # taken from http://mirror.centos.org/centos/6/os/x86_64/Packages/libicu-4.2.1-9.1.el6_2.x86_64.rpm

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
This is standard [Python 3](http://www.python.org) code; however, there are a few important points to note around file handling and configuring the root directory.

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

We use the [StackHut runtime functions](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) to aid file handling within the service - this includes the function  `stackhut.put_file()` that transparently upload files to cloud storage. Files are processed within the current working directory; this is unique to each request and flushed upon request completion. Files themselves live on the cloud for approximately a few hours before being removed.

#### Root Directory

We use the [StackHut runtime functions](http://stackhut.readthedocs.org/en/latest/creating_service/service_runtime.html) to obtain the location of the service on the filesystem from `stackhut.root_dir`. This is used to reference embedded resource files, in this case the `phantomjs` binary as needed by Selenium.

