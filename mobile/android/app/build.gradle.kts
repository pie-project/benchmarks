import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
val llamaCppDir: String? = localProps.getProperty("llama.cpp.dir")
val llamaCppTag = "b11312"
val llamaGpu: String = (project.findProperty("llamaGpu") as String?)
    ?: if (localProps.getProperty("vulkan.headers.dir") != null) "vulkan" else "none"

val pieAars = fileTree("libs/pie") { include("*.aar", "*.jar") }
val mlcLibs = file("libs/mlc")
val hasPie = !pieAars.isEmpty && file("src/pie/kotlin").exists()
val hasMlc = file("libs/mlc/mlc4j/output/tvm4j_core.jar").exists() && file("src/mlc/kotlin").exists()

android {
    namespace = "org.pieevals.phonebench"
    compileSdk {
        version = release(37) { minorApiLevel = 2 }
    }
    ndkVersion = "28.2.13676358"

    defaultConfig {
        applicationId = "org.pieevals.phonebench"
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        ndk { abiFilters += "arm64-v8a" }
        buildConfigField("String", "LLAMA_CPP_TAG", "\"$llamaCppTag\"")
        buildConfigField("String", "LLAMA_GPU", "\"$llamaGpu\"")
        buildConfigField("boolean", "HAS_PIE", "$hasPie")
        buildConfigField("boolean", "HAS_MLC", "$hasMlc")
        externalNativeBuild {
            cmake {
                arguments += listOf(
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DLLAMA_CPP_TAG=$llamaCppTag",
                    "-DLLAMA_GPU=$llamaGpu",
                    "-DANDROID_STL=c++_shared",
                )
                if (llamaCppDir != null) arguments += "-DLLAMA_CPP_DIR=$llamaCppDir"
                localProps.getProperty("vulkan.headers.dir")?.let { arguments += "-DLLAMA_VULKAN_HEADERS=$it" }
                localProps.getProperty("spirv.headers.cmake.dir")?.let { arguments += "-DLLAMA_SPIRV_HEADERS_DIR=$it" }
            }
        }
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.31.6"
        }
    }

    sourceSets {
        getByName("main") {
            assets.srcDir(rootProject.file("../shared"))
            kotlin.srcDir(if (hasPie) "src/pie/kotlin" else "src/nopie/kotlin")
            kotlin.srcDir(if (hasMlc) "src/mlc/kotlin" else "src/nomlc/kotlin")
            if (hasMlc) {
                java.srcDir("src/mlc/java")
                jniLibs.srcDir("libs/mlc/mlc4j/output")
            }
        }
    }

    packaging {
        jniLibs.useLegacyPackaging = true
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.09.00")
    implementation(composeBom)
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.9.4")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")
    implementation("com.google.ai.edge.litertlm:litertlm-android:0.19.1")
    if (hasPie) {
        implementation(pieAars)
        implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
        implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.11.0")
        implementation("org.msgpack:msgpack-core:0.9.12")
        implementation("com.squareup.okhttp3:okhttp:4.12.0")
    }
    if (hasMlc) implementation(files("libs/mlc/mlc4j/output/tvm4j_core.jar"))
}
