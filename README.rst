======
picGaz
======

Gather pictures from folders to a destination folder, esp. used for collecting windows 10 logon background pictures in one step.

Origins
=======

The Windows 10 operating system loads a beautiful image as a background image when you log in.

This image is updated from time to time.

The image is temporarily stored in a specific system directory, by default it's ``C:/Users/{Username}/AppData/Local/Packages/Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy/LocalState/Assets`` .

This script is used to read, analyze, filter, count, compare and copy the files in this directory and other processes to collect these images automatically.

After abstracting the above steps, it can be applied to the collection of images from any given directory.

Also, it can be used for image file de-duplication (currently based on hash determination).

USAGE
===================

1. edit ``picGaz.conf.yml``
2. execute ``picGaz.py``

Thoughts
========

Whenever I create such practical scripts, I can't stop thinking about one thing:

    What is often a very simple operation for humans often becomes extremely complicated when it is left to computers. In a simple image collection progress, the computer needs to make complex rule conversions for some judgments that humans make only in an instant.

    Conversely, some of the very complex operations for humans, but for the computer is exceptionally simple.

    What an interesting thing!
