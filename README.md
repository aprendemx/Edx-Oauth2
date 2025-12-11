# LlaveMX OAuth2 backend for Open edX

OAuth2 backend para integrar Open edX (Tutor) con LlaveMX.
Proporciona autenticación, asociación por CURP y un mecanismo para exponer datos completos al MFE sin modificar el core de Open edX.

## Descripción general

Este proyecto implementa:

- **Backend OAuth2** basado en python-social-auth para LlaveMX.
- **Pipeline extendido** para asociar usuarios mediante CURP utilizando ExtraInfo.
- **Mecanismos para preservar y exponer** los detalles completos de LlaveMX al MFE.
- **Un AppConfig** que inserta dinámicamente los pasos requeridos en el SOCIAL_AUTH_PIPELINE y aplica parches controlados para el MFE.
- **Un plugin de Tutor** para registrar el backend, credenciales y ajustes de CORS/CSRF.

La integración opera únicamente mediante configuración y runtime patching. No requiere editar código del core de Open edX.

## Instalación en Tutor

### 1. Instalar el backend mediante OPENEDX_EXTRA_PIP_REQUIREMENTS

En `config.yml`:

```yaml
OPENEDX_EXTRA_PIP_REQUIREMENTS:
  - git+https://github.com/aprendemx/Edx-Oauth2.git@main
```

Esto instala:
- `oauth2_llavemx`
- El formulario de registro personalizado
- Dependencias externas necesarias

### 2. Instalar y habilitar el plugin de Tutor

Colocar el archivo del plugin, por ejemplo:

```
/opt/tutor-plugins/oauth2_llavemx/oauth2_llavemx.yml
```

El plugin se encarga de:

- Registrar `oauth2_llavemx.llavemx_oauth.LlaveMXOAuth2` en AUTHENTICATION_BACKENDS.
- Declarar THIRD_PARTY_AUTH_BACKENDS únicamente en LMS.
- Registrar credenciales LlaveMX (SOCIAL_AUTH_LLAVEMX_*).
- Añadir dominios de CORS/CSRF permitidos.
- Registrar la App Django del backend mediante:
  ```python
  INSTALLED_APPS.append("oauth2_llavemx.apps.OAuth2LlaveMXConfig")
  ```

Habilitación:

```bash
tutor plugins enable oauth2_llavemx
```

### 3. Construcción y despliegue

```bash
tutor images build openedx
tutor images build mfe
tutor local restart lms mfe
```

## Pipeline incluido en el backend

El paquete implementa dos pasos personalizados para el pipeline de autenticación:

### associate_by_curp

- Se ejecuta exclusivamente cuando el backend activo es LlaveMX.
- Realiza asociación automática mediante la CURP almacenada en `custom_reg_form.ExtraInfo`.
- No interfiere con Studio ni con otros backends.

### preserve_llavemx_details

- Reinyecta todos los detalles obtenidos desde LlaveMX dentro del pipeline.
- Guarda la información también en sesión bajo la clave `llavemx_details`.
- Permite que el MFE reciba datos completos incluso si Open edX aplica filtrado a `pipeline_user_details`.

## Mecanismos adicionales aplicados por la AppConfig

Dado que Open edX reescribe SOCIAL_AUTH_PIPELINE y filtra campos antes del MFE, la AppConfig del backend realiza parches controlados en tiempo de ejecución que no requieren modificar archivos del core:

- **Inserción dinámica** de los pasos del pipeline antes de `common.djangoapps.third_party_auth.pipeline.ensure_user_information`.
- **Wrapper para get_auth_context y get_mfe_context**, restaurando `pipeline_user_details` a partir de `llavemx_details` si el core los elimina.
- **Reemplazo del método ContextDataSerializer.get_pipelineUserDetails** para exponer los campos completos sin truncamiento.

Todos estos parches son locales al backend y no afectan otras integraciones.

## Integración con MFE

El MFE recibe la información completa enviada por LlaveMX, incluyendo:

- Nombre y apellidos
- CURP
- Datos de nacimiento
- Contacto
- Campos adicionales usados por el formulario personalizado

El backend asegura que esta información esté disponible tanto durante el proceso de autenticación como en formularios posteriores.

## Flujo de desarrollo

- El código del backend se desarrolla localmente en macOS.
- Los cambios se versionan en el repositorio correspondiente.
- Las pruebas se ejecutan en la máquina virtual donde está instalado Tutor.
- El plugin de settings se encuentra en `/opt/tutor-plugins/`.
- Los builds de imágenes reproducen consistentemente la integración desde los repositorios.


## License

MIT License. See `LICENSE`.
