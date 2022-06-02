# SeaDarQ Fetcher

## Purpose
Seadarq Fetcher's task is to constantly watch if some files were changed by SeaDarQ.  
- If the radar picture (image.tif, geotiff.tif) has changed, Fetcher creates a GeoJSON object from them,  
and place the Json and the *.tif to a Zip file and upload it to radarserv.  
- If the targets.txt file changed, it sends the new or updated tagets to Hermes.

## Architecture
![ONE](docs/pics/halico.png)  
Blue lines are function calls, Red line is a hook handled by apto framework, green lines are message sending, receiving from to Hermes.  
  
## Defaul Config
### Folders and Radar Server
Currently there are two folders what the software is monitoring.
- name: SeaDarQ Lab RGBA  
  path: /mnt/seadarq/  
  picture name: image.tif
  target name: targets.txt
- name: SeaDarQ Lab 16bit  
  path: /mnt/seadarq/  
  picture name: geotiff.tif
  target name: targets.txt

Both of them are published (the ZIP file with the tif image and the calculated Feature GeoJSON)  
to the same radarserver but different directories.
Radar Server config: host: sc, port: 2121

- SeaDarQ Lab RGB/image.tif --> /seadarq/
- SeaDarQ Lab 16bit/geotiff.tif --> /seadarq-16/

### Hermes
- url: amqp://user:pass@host:5672/vhost
- sevice name: seadarq-fetcher
#### Health Publisher
- exchange name: cache.event
- routing key: cache.set.health.seadarq-fetcher
#### Publish Target
- exchange name: feature
- routing key: seadarq-fetcher.update or seadarq-fetcher.delete
#### Publish Notification
- exchange name: theia
- routing key: notification.general
