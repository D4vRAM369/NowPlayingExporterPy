package com.d4vram.nowplayingexporterpy

import com.topjohnwu.superuser.Shell

object RootHelper {
    fun init() {
        Shell.enableVerboseLogging = false
        Shell.setDefaultBuilder(
            Shell.Builder.create()
                .setFlags(Shell.FLAG_MOUNT_MASTER or Shell.FLAG_REDIRECT_STDERR)
                .setTimeout(10_000)
        )
    }
    fun isRootAvailable(): Boolean = try { Shell.getShell().isRoot } catch (_: Throwable) { false }

    fun exec(vararg commands: String): Shell.Result = Shell.cmd(*commands).exec()

    fun findFirstExistingPath(candidates: List<String>): String? {
        val cmd = candidates.joinToString(" ; ") { p -> "[ -f \"$p\" ] && echo \"$p\"" }
        val res = exec(cmd)
        return res.out.firstOrNull()?.trim().takeIf { !it.isNullOrEmpty() }
    }

    fun copyFileAsRoot(src: String, dstAbs: String): Boolean {
        val res = exec(
            "mkdir -p \"${dstAbs.substringBeforeLast('/')}\"",
            "cp -f \"$src\" \"$dstAbs\"",
            "chmod 0644 \"$dstAbs\""
        )
        return res.isSuccess
    }
}
