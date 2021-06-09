# Rules Ideas

```yaml
channel_mapping : {VEOG:EOG}                                      
CHANNEL_TYPES:[]
CHANNELS:[FPZ,]
TYPES:[]
line_freq : 50
script_1 : "raw.set_channel_mapping({VEOG:EOG})"

path
canales
{EOG:[VEOG,HEOG]}
```

- opcion 1: heuristica para patrones repetidos a nivel general (nombres de canales oculares por ejemplo)
- opcion 2: aprender de un ejemplo dado por el usuario (se hace la inferencia con mne-bids, se guarda, el usuario inspecciones y corrige, releemos e inferimos los cambios)
- opción 3: estos cambios esten en el archivo de reglas