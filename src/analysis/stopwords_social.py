"""
Stop words para análisis social (word clouds, top words, temas).
Una sola fuente de verdad: EN + ES + ruido de comentarios.
NO incluir palabras con carga sentimental (love, hate, great, bad, etc.).
"""

# Inglés: artículos, pronombres, preposiciones, auxiliares, conectores
_EN_STRUCTURAL = {
    "the", "a", "an", "and", "or", "but", "if", "of", "in", "to", "for", "with",
    "on", "at", "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "this", "that", "these", "those", "it", "its", "i", "you", "he", "she", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "our", "their",
    "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "some", "any",
    "other", "another", "same", "such", "only", "own", "just", "also",
    "not", "no", "yes", "so", "than", "too", "very", "into", "onto", "over",
    "about", "after", "before", "during", "through", "between", "under",
    "here", "there", "then", "now", "well", "back", "out", "up", "down",
    "get", "gets", "got", "getting", "make", "makes", "made", "making",
    "say", "says", "said", "saying", "tell", "tells", "told", "think", "thinks", "thought",
    "know", "knows", "knew", "known", "want", "wants", "wanted", "going", "way",
    "one", "ones", "thing", "things", "something", "anything", "everything", "nothing",
    "really", "even", "still", "already", "perhaps", "maybe", "actually", "basically",
    "literally", "though", "although", "however", "while", "because", "since",
    "mean", "means", "meant", "ask", "asked", "asking", "can", "probably", "experience",
}

# Español: artículos, pronombres, preposiciones, verbos auxiliares
_ES_STRUCTURAL = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero", "si", "no",
    "que", "de", "a", "en", "es", "se", "te", "le", "lo", "al", "del", "por", "con",
    "para", "su", "sus", "como", "mas", "más", "muy", "ya", "sin", "hay", "qué",
    "cuando", "donde", "quien", "cual", "cuales", "todo", "toda", "todos", "todas",
    "esta", "este", "estas", "estos", "esa", "ese", "esas", "esos", "otra", "otro", "otros", "otras",
    "nos", "me", "mi", "tu", "ti", "aqui", "asi", "solo", "tambien", "entre", "desde", "hasta",
    "durante", "contra", "sobre", "tras", "ser", "era", "fue", "son", "han", "tiene", "tienen",
    "tengo", "tienes", "puede", "pueden", "creo", "porque", "aunque", "pues", "entonces",
    "ver", "vi", "visto", "veo", "mirar", "mirando", "miré", "película", "películas",
    "quién", "cómo", "cuándo", "dónde", "cuál", "por qué",
}

# Contexto cine/redes: genéricos que no discriminan para insights de marketing
_MOVIE_GENERIC = {
    "movie", "film", "films", "movies", "cinema", "theater", "theatre",
    "watch", "watched", "watching", "watches", "see", "sees", "saw", "seen",
    "view", "views", "viewed", "viewing", "look", "looks", "looked", "looking",
    "video", "videos", "clip", "clips", "trailer", "trailers",
}

# Ruido típico en comentarios (Reddit, YouTube, etc.)
_SOCIAL_NOISE = {
    "https", "http", "www", "com", "org", "net", "html", "sportsmobile",
    "lol", "lols", "lmao", "haha", "hahaha", "xd", "omg", "wtf", "idk", "imo", "tbh",
    "btw", "etc", "hey", "oh", "uh", "um", "yeah", "nah", "ok", "okay",
    "right", "left", "first", "last", "new", "old", "long", "big", "small",
    "real", "really", "like", "get", "one", "way", "thing", "things",
}

# Unión final: no incluir palabras con sentimiento (love, hate, great, amazing, etc.)
SOCIAL_STOP_WORDS: frozenset = frozenset(
    _EN_STRUCTURAL
    | _ES_STRUCTURAL
    | _MOVIE_GENERIC
    | _SOCIAL_NOISE
)
