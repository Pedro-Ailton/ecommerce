//Index/Admin
function scrollProdutos(direcao) {
        const container = document.getElementById('produtos');
        const scrollStep = 375; // você pode aumentar esse valor se quiser que pule mais produtos
        container.scrollBy({
        left: direcao * scrollStep,
        behavior: 'smooth'
        });
    }

    
    let slideAtual = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        const slidesContainer = document.getElementById('slides');

        function mostrarSlide(index) {
            slideAtual = (index + totalSlides) % totalSlides;
            slidesContainer.style.transform = 'translateX(' + (-slideAtual * 100) + '%)';
        }

        function mudarSlide(n) {
            mostrarSlide(slideAtual + n);
            reiniciarAutoSlide();  // Reinicia o temporizador ao clicar no botão
        }

        // Auto slide
        let intervalo = setInterval(() => mudarSlide(1), 5000); // a cada 5 segundos

        function reiniciarAutoSlide() {
            clearInterval(intervalo);
            intervalo = setInterval(() => mudarSlide(1), 5000);
        }

        window.onload = () => mostrarSlide(slideAtual);

//forms
