import Header from '@/components/Header'
import ClientOnlyPage from '@/components/ClientOnlyPage'

const HomePage: React.FC = () => {
  return (
    <div>
      <Header />
      <main className="p-8">
        <ClientOnlyPage />
      </main>
    </div>
  )
}

export default HomePage