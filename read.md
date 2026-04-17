Tenemos una aplicación de escritorio desarrollada en python y tkinter para la capa de visualización.
Las funcionalidades principales del sistema son:
    -quitarle esfuerzo a lo entrenadores de nuestra empresa con el seguimiento de sus atletas
    -Sobretodo nos centramos en la parte del antes y despues. Para ello tomamos las fotos de los cuadernos de entrenamiento de 
    los atletas. El objetivo de la aplicación es tomar esas fotos usar un OCR para extraer el texto y usar la ia para detectar
    el progreso del atleta y crear un excel o csv para poder compararlo con los datos anteriores y ver el progreso del atleta.
    -Por otro lado realizaremos que se ingresen los datos de los formularios de seguimiento semanales de los atletas.
    todos estos datos los almacenaremos en una base de datos local en sqlite. De esos datos almacenados mostraremos una comparativa entre la semana anterior con la actual además de destacar la peor y mejor semana.

    Las páginas serán:
    -Dashboard: será la página principal, mostrará el número de atletas, formularios pendientes y un calendario de llamadas por si
    al entrenador le interesa tenerlo todo en nuestra app.
    -Listado de atletas: mostrará todos los atletas y permitirán crear nuevos atletas, Y entrar a la ficha individual de cada atleta
    -Ficha individual: mostrará el nombre del atleta, los datos de los formularios de seguimiento semanales y acceso a cargar rutinas o introducir el progreso semanal. Además de contener los datos de seguimineto semanal.
    -Carga de archivos: aquí es donde el entrenador podrá cargar las fotos de los cuadernos de entrenamiento para que el sistema procese.

    Para el analisis de texto usaremos pytesseract, para la gestión de base de datos usaremos SQLAlchemy, para la interface usaremos customtkinter y para analizar el texto del OCR usaremos Gliner para la extraccion de datos ya que es un modelo pequeño y eficiente para esta tarea simple.

    


    
 
    