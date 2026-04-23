default:
	uvicorn app:app & \
	\ls docs/*.puml | entr -c sh -c 'plantuml -tpng docs/*.puml'
