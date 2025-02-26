#Vérifier l’état du cluster
hdfs dfsadmin -safemode get

#Télécharger un fichier depuis HDFS vers local
hdfs dfs -get /user/etudiant/data/mon_fichier.txt ./

