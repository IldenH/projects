default:
	uvicorn app:app & \
	live-server --host 127.0.0.1 -o & \
	\ls docs/*.puml | entr -c sh -c 'plantuml -tpng docs/*.puml'
