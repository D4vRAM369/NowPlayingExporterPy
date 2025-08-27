plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.d4vram.nowplayingexporterpy"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.d4vram.nowplayingexporterpy"
        minSdk = 28
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"

        // Requisito de Chaquopy: declarar ABI
        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }

    // 👇 ESTE es el bloque que te fallaba: debe ir *dentro* de android { }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

// No necesitas pip; si algún día lo usas en Kotlin DSL:
// extensions.configure<com.chaquo.python.PythonExtension>("python") {
//     pip { install("numpy==1.26.4") }
// }

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")

    // Root (desde JitPack, recuerda tener jitpack en settings.gradle.kts)
    implementation("com.github.topjohnwu.libsu:core:5.2.2")
    implementation("com.github.topjohnwu.libsu:service:5.2.2")

    // Tests opcionales
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
