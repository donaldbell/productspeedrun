# The app component: everything in src/, the shared code in ../../common, and the generated pins.h (../include).
FILE(GLOB_RECURSE app_sources ${CMAKE_SOURCE_DIR}/src/*.c ${CMAKE_SOURCE_DIR}/../common/*.c)
idf_component_register(SRCS ${app_sources}
                       INCLUDE_DIRS "." "../include" "../../common"
                       PRIV_REQUIRES esp_driver_gpio esp_driver_i2s esp_driver_ledc esp_driver_rmt esp_adc
                                     esp_wifi esp_netif esp_event nvs_flash esp_timer)
