# avebot

le canzoni vengono salvate nella directory /home/ave/avebot/music.
per evitare che il server si innondi, queste vengono cancellate ogni sera alle 4.

lo faccio con il seguente programma:
	crontab -e
e la seguente script:
	0 4 * * * rm /home/ave/avebot/music/*

per far girare il bot 24/7 uso:
	nohup python3 avebot.py &
