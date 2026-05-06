import io
import hashlib
from PIL import Image, ImageDraw
import customtkinter as ctk

class MediaService:
    """
    Servicio encargado de la gestión de medios, como avatares y procesamiento de fotos.
    """
    _cache_imagenes: dict = {}

    @classmethod
    def obtener_avatar_atleta(cls, atleta_id: int, foto_bytes: bytes | None, nombre: str, size=(60, 60)) -> ctk.CTkImage:
        """
        Devuelve una CTkImage del atleta con gestión de caché.
        """
        clave_hash = hashlib.md5(foto_bytes).hexdigest() if foto_bytes else None
        clave = (atleta_id, clave_hash)
        
        if clave not in cls._cache_imagenes:
            img = None
            if foto_bytes:
                try:
                    img = Image.open(io.BytesIO(foto_bytes)).resize(size, Image.LANCZOS)
                except Exception as e:
                    logger.warning(f"Error cargando foto para atleta {atleta_id}: {e}")
            
            # Si no hay imagen o falló la carga, crear la de por defecto
            if not img:
                img = cls.crear_avatar_por_defecto(nombre, size)
            
            cls._cache_imagenes[clave] = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            
        return cls._cache_imagenes[clave]

    @staticmethod
    def crear_avatar_por_defecto(nombre: str, size=(60, 60)) -> Image.Image:
        """Genera un avatar con la inicial del nombre sobre un fondo colorido."""
        img = Image.new('RGB', size, color=(60, 80, 140))
        d = ImageDraw.Draw(img)
        letra = nombre[0].upper() if nombre else "?"
        # Posicionamiento básico de la letra
        d.text((size[0]//3, size[1]//4), letra, fill=(255, 255, 255))
        return img
