import { writable } from "svelte/store"
import ePub from "epubjs"

// Book interface 
export interface Book {
    id: string
    file: File
    coverUrl: string
    title: string
}


class BookStoreService {
    #store = writable<Book[]>([])

    public readonly subscribe = this.#store.subscribe

    public async addBook(book: File): Promise<void> {
        try {
            const processedBook = await this.#processEpubFile(book)
            this.#store.update(books => {
                // Prevent ducplicates
                if (books.some(b => b.id === processedBook.id)) {
                    // get dupblicated so we respond with the same array
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
    #processEpubFile(book: File): Promise<Book> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()

            reader.onload = async () => {
                try {
                    const bookingStance = ePub(reader.result as ArrayBuffer)
                    const metadata = await bookingStance.loaded.metadata
                    const coverUrl = await bookingStance.coverUrl()

                    bookingStance.destroy()

                    resolve({
                        id: book.name,
                        file: book,
                        coverUrl: coverUrl || '',
                        title: metadata.title || 'Unknow Title'
                    })

                } catch (error) {
                    // Epub filed! reject
                    reject(error)
                }
            }
        })
    }

}

export const bookStore = new BookStoreService()
