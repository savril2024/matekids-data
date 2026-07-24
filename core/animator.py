"""
core/animator.py
Responsable de ANIMAR los elementos visuales.
Compatible con Flet 0.86+
"""
import asyncio
import flet as ft
from core.visual_renderer import VisualRenderer


class Animator:
    """Aplica animaciones a los objetos visuales."""
    
    def __init__(self, renderer: VisualRenderer):
        self.renderer = renderer

    async def animate_remove(self, objects_view: ft.Column, n: int, page: ft.Page):
        """Anima la remoción de objetos (fade out + shrink)."""
        # Obtener todos los objetos de todas las filas
        all_objects = []
        for control in objects_view.controls:
            if isinstance(control, ft.Row):
                all_objects.extend(control.controls)
        
        to_remove = all_objects[-n:] if len(all_objects) >= n else all_objects
        
        # Animar fade out
        for obj in to_remove:
            if hasattr(obj, 'opacity'):
                obj.opacity = 0.3
                obj.scale = 0.5
                page.update()
                await asyncio.sleep(0.35)
        
        # Remover de las filas
        for obj in to_remove:
            for control in objects_view.controls:
                if isinstance(control, ft.Row) and obj in control.controls:
                    control.controls.remove(obj)
        
        page.update()
        await asyncio.sleep(0.30)

    async def animate_add(self, objects_view: ft.Column, emoji: str, n: int, page: ft.Page):
        """Anima la adición de objetos (pop-in effect)."""
        # Obtener la última fila o crear una nueva
        if objects_view.controls and isinstance(objects_view.controls[-1], ft.Row):
            target_row = objects_view.controls[-1]
        else:
            target_row = ft.Row(wrap=True, spacing=5, alignment=ft.MainAxisAlignment.CENTER)
            objects_view.controls.append(target_row)
        
        for _ in range(n):
            new_obj = self.renderer.make_emoji(emoji, size=35)
            new_obj.scale = 0
            new_obj.opacity = 0
            
            target_row.controls.append(new_obj)
            page.update()
            await asyncio.sleep(0.30)
            
            new_obj.scale = 1.3
            new_obj.opacity = 1
            page.update()
            await asyncio.sleep(0.30)
            
            new_obj.scale = 1
            page.update()

    async def animate_multiply(self, objects_view: ft.Column, page: ft.Page):
        """Resalta cada grupo secuencialmente (efecto de zoom)."""
        # Los grupos ya están en la primera fila
        if not objects_view.controls:
            return
        
        first_row = objects_view.controls[0]
        if not isinstance(first_row, ft.Row):
            return
        
        for group in first_row.controls:
            if isinstance(group, ft.Container) and isinstance(group.content, ft.Row):
                # Resaltar grupo
                for obj in group.content.controls:
                    if hasattr(obj, 'scale'):
                        obj.scale = 1.3
                page.update()
                await asyncio.sleep(0.50)
                
                # Volver a tamaño normal
                for obj in group.content.controls:
                    if hasattr(obj, 'scale'):
                        obj.scale = 1
                page.update()

    async def animate_divide(self, objects_view: ft.Column, emoji: str, divisor: int, page: ft.Page):
        """
        Animación de división: reorganiza los objetos en cajas.
        NO borra los objetos, los mueve visualmente.
        """
        # 1. Obtener todos los objetos existentes
        all_objects = []
        for control in objects_view.controls:
            if isinstance(control, ft.Row):
                all_objects.extend(control.controls)
        
        total_objects = len(all_objects)
        
        if total_objects == 0:
            return
        
        # 2. Validar división exacta
        if total_objects % divisor != 0:
            raise ValueError(f"No se puede repartir {total_objects} objetos entre {divisor} grupos.")
        
        # 3. Limpiar vista
        objects_view.controls.clear()
        
        # 4. Crear estructura: fila de origen + espaciador + fila de cajas
        source_row = ft.Row(wrap=True, spacing=5, alignment=ft.MainAxisAlignment.CENTER)
        source_row.controls.extend(all_objects)
        
        spacer = ft.Container(height=30)
        
        groups_row = ft.Row(wrap=True, spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        group_containers = []
        
        for i in range(divisor):
            container = ft.Container(
                content=ft.Row(spacing=3, wrap=True),
                border=ft.BorderSide(width=3, color=ft.Colors.PURPLE),
                border_radius=15,
                padding=15,
                bgcolor=ft.Colors.PURPLE_50,
                width=120,
                height=120,
            )
            group_containers.append(container)
            groups_row.controls.append(container)
        
        objects_view.controls = [source_row, spacer, groups_row]
        page.update()
        
        await asyncio.sleep(0.50)
        
        # 5. Mover objetos uno por uno a las cajas
        objects_per_group = total_objects // divisor
        
        for obj_idx, obj in enumerate(all_objects):
            group_idx = obj_idx // objects_per_group
            target_container = group_containers[group_idx]
            
            # Animar movimiento
            obj.scale = 0.7
            obj.opacity = 0.5
            page.update()
            await asyncio.sleep(0.45)
            
            # Mover físicamente
            if obj in source_row.controls:
                source_row.controls.remove(obj)
            
            if isinstance(target_container.content, ft.Row):
                obj.scale = 0.5
                target_container.content.controls.append(obj)
                page.update()
                await asyncio.sleep(0.30)
                
                obj.scale = 1.2
                page.update()
                await asyncio.sleep(0.45)
                
                obj.scale = 1.0
                obj.opacity = 1.0
                page.update()
                await asyncio.sleep(0.30)
        
        # 6. Limpiar fila de origen si está vacía
        await asyncio.sleep(0.3)
        if not source_row.controls:
            objects_view.controls.remove(source_row)
            objects_view.controls.remove(spacer)
        
        page.update()