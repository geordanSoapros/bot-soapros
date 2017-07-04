#Script de reinicio del bot
echo "Iniciando script para el reinicio automatico del bot"
#ruta_base= '/home/AIML/pyaiml3'
mv bot_brain.brn bot_brain_old.brn
#test ! -f $ruta_base/bot_brain.brn rm bot_brain.brn && echo "no se encontró el archivo"
#echo "Borrando Brain"
#rm bot_brain.brn
#echo "No existe brain, creando"
echo "Iniciando server flask"
screen python server.py