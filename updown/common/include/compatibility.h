/*
A set of compatibility macros between gcc and clang
*/

#if defined(__clang__)
#define OPTNONE __attribute__((optnone))
#elif defined(__GNUC__) || defined(__GNUG__)
#define OPTNONE __attribute__((optimize("O0")))
#else
#define OPTNONE
#endif

#define MACRO_STRINGIFY(s) #s
#define MACRO_JOIN(x, y) MACRO_STRINGIFY(x##y)
#define MACRO_DO_PRAGMA(x) _Pragma(#x)
#define MACRO_PRAGMA(compiler, x) MACRO_DO_PRAGMA(compiler diagnostic ignored x)
// must have a PopWarning at the end of the file to turn the warning back on
#if defined(__clang__)
#define PUSHWARNING(warning) _Pragma("clang diagnostic push") MACRO_PRAGMA(clang, MACRO_JOIN(-W, warning))
#elif defined(__GNUC__) || defined(__GNUG__)
#define PUSHWARNING(warning) _Pragma("GCC diagnostic push") MACRO_PRAGMA(GCC, MACRO_JOIN(-W, warning))
#else
#define PUSHWARNING(warning)
#endif

#if defined(__clang__)
#define POPWARNING _Pragma("clang diagnosti pop")
#elif defined(__GNUC__) || defined(__GNUG__)
#define POPWARNING _Pragma("GCC diagnostic pop")
#else
#define POPWARNING
#endif
