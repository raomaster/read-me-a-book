import { writable } from "svelte/store"
import ePub from "epubjs"

// Book interface 
export interface Book {
    id: string
    file: File
    coverUrl: string
    title: string
    data: ArrayBuffer
}


class BookStoreService {
    #store = writable<Book[]>([])

    public readonly subscribe = this.#store.subscribe

    public async addBook(bookFile: File): Promise<void> { // Cambiado el nombre del parámetro para claridad
        try {
            const processedBook = await this.#processEpubFile(bookFile)
            this.#store.update(books => {
                // Prevent duplicates
                if (books.some(b => b.id === processedBook.id)) {
                    // get duplicated so we respond with the same array
                    return books
                }
                // if not duplicate we respond with the array + new book
                return books.concat(processedBook)
            })

        } catch(error) {
            console.error("Failed to process and add book: ", error)
        
        }
    }
    
    // Generate an Epub Object with the file and metadata 
    #processEpubFile(bookFile: File): Promise<Book> { // Cambiado el nombre del parámetro
        return new Promise((resolve, reject) => {
            const reader = new FileReader()

            reader.onload = async () => {
                try {
                    console.log('BookStore: FileReader onload. reader.result type:', typeof reader.result, 'reader.result:', reader.result); // <-- DEBUG LOG
                    
                    const arrayBuffer = reader.result as ArrayBuffer; // Guardar el ArrayBuffer
                    const bookInstance = ePub(arrayBuffer) // Usar ArrayBuffer para epubjs
                    const metadata = await bookInstance.loaded.metadata
                    const coverUrl = await bookInstance.coverUrl() // Esto puede devolver null

                    bookInstance.destroy() // Importante para liberar recursos

                    resolve({
                        id: bookFile.name,
                        file: bookFile,
                        coverUrl: coverUrl || '', // Asegurar que sea una cadena, incluso si es vacía
                        title: metadata.title || 'Unknown Title', // Título por defecto y corrección tipográfica
                        data: arrayBuffer // <--- AÑADIR ESTO: Guardar el ArrayBuffer en el objeto Book
                    });
                    console.log('BookStore: #processEpubFile resolved for:', bookFile.name, 'with title:', metadata.title); // Log de éxito


                } catch (error) {
                    // Epub failed! reject
                    console.error("Error processing EPUB with epubjs:", error);
                    reject(error)
                }
            }

            reader.onerror = () => {
                console.error("FileReader error reading file:", reader.error);
                reject(reader.error || new Error("FileReader failed to read the file."));
            }

            reader.readAsArrayBuffer(bookFile) // Leer el archivo como ArrayBuffer. Movido dentro de la Promise.
        })
    }

}
export const bookStore = new BookStoreService()
