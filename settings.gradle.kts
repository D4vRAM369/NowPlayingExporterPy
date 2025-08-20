pluginManagement {
    repositories {
        google()
        mavenCentral()
        maven(url = "https://chaquo.com/maven")
        gradlePluginPortal()
    }
    plugins {
        id("com.android.application") version "8.5.0"
        id("org.jetbrains.kotlin.android") version "1.9.24"
        id("com.chaquo.python") version "15.0.1"
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven(url = "https://chaquo.com/maven")
        maven(url = "https://jitpack.io") // For libsu
    }
}

rootProject.name = "NowPlayingExporterPy"
include(":app")
